#!/usr/bin/env python3
"""
XMLスクリプトからGoogle Cloud Text-to-Speech APIを使って音声合成を行うスクリプト

使用方法:
1. Google Cloudのサービスアカウントキーを取得し、環境変数 GOOGLE_APPLICATION_CREDENTIALS に設定
2. config.yamlを設定する
3. python googletts_processor.py [オプション] を実行する
"""


import os
import re
import json
import time
import logging
import yaml
import hashlib
import click
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Dict, List, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import texttospeech
from pydub import AudioSegment


class GoogleTTSProcessor:
    """XMLスクリプトをGoogle TTSで音声合成するプロセッサ"""

    def __init__(self, config_path: str = "config.yaml", paragraph_ids: Optional[List[str]] = None):
        """
        初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.tts_client = texttospeech.TextToSpeechClient()
        self.tts_params = self.config.get('google_tts', {})
        self.paragraph_ids = paragraph_ids

    def _load_config(self, config_path: str) -> Dict:
        """設定ファイルを読み込み"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイル {config_path} が見つかりません")
        except yaml.YAMLError as e:
            raise ValueError(f"設定ファイルの読み込みエラー: {e}")

    def _setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=getattr(logging, self.config['logging']['level']),
            format=self.config['logging']['format']
        )
        self.logger = logging.getLogger(__name__)

    def check_google_tts_connection(self) -> bool:
        """Google TTS APIの接続確認"""
        try:
            # シンプルなテスト用音声合成を実行
            input_text = texttospeech.SynthesisInput(text="テスト")
            voice = texttospeech.VoiceSelectionParams(
                language_code=self.tts_params.get('language_code', 'ja-JP'),
                name=self.tts_params.get('voice_name', 'ja-JP-Standard-D')
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=getattr(texttospeech.AudioEncoding, self.tts_params.get('audio_encoding', 'LINEAR16'))
            )

            response = self.tts_client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config
            )

            if response.audio_content:
                self.logger.info("Google TTS API接続成功")
                return True
            else:
                self.logger.error("Google TTS API接続失敗: 音声データが返されませんでした")
                return False
        except Exception as e:
            self.logger.error(f"Google TTS API接続エラー: {e}")
            return False

    def parse_xml_script(self, xml_path: str) -> Tuple[List[Dict], List[Tuple[str, int, str]]]:
        """
        XMLスクリプトをパースして段落情報とスライド遷移情報を抽出

        Args:
            xml_path: XMLファイルのパス

        Returns:
            (段落情報のリスト, スライド遷移情報のリスト[(paragraph_id, slide_number, slide_title)])
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            paragraphs = []
            slide_transitions = []
            current_slide_info = None

            for element in root:
                if element.tag == 'paragraph':
                    paragraph_id = element.get('id')
                    if not paragraph_id:
                        continue

                    # テキスト内容を取得（ポーズタグなどを処理）
                    text = self._extract_text_content(element)

                    if text.strip():  # 空でないテキストのみ処理
                        paragraph_data = {
                            'id': paragraph_id,
                            'text': text,
                            'original_xml': ET.tostring(element, encoding='unicode')
                        }

                        # スライド情報を関連付け
                        if current_slide_info:
                            paragraph_data['slide_number'] = str(current_slide_info[0])
                            paragraph_data['slide_title'] = current_slide_info[1]
                            slide_transitions.append((paragraph_id, current_slide_info[0], current_slide_info[1]))
                            current_slide_info = None  # 一度使ったらリセット

                        paragraphs.append(paragraph_data)

                elif element.tag == 'slide_transition':
                    slide_number = element.get('slide_number')
                    slide_title = element.get('slide_title', '')
                    if slide_number:
                        try:
                            current_slide_info = (int(slide_number), slide_title)
                        except ValueError:
                            self.logger.warning(f"不正なスライド番号: {slide_number}")

            self.logger.info(f"XMLファイル {xml_path} から {len(paragraphs)} 個の段落、{len(slide_transitions)} 個のスライド遷移を抽出")
            return paragraphs, slide_transitions

        except ET.ParseError as e:
            self.logger.error(f"XMLパースエラー: {e}")
            return [], []
        except Exception as e:
            self.logger.error(f"XMLファイル処理エラー: {e}")
            return [], []

    def _extract_text_content(self, paragraph_element) -> str:
        """
        段落要素からテキスト内容を抽出（ポーズタグを適切に処理）

        Args:
            paragraph_element: 段落のXML要素

        Returns:
            処理されたテキスト
        """
        text_parts = []

        # 要素の直接のテキスト
        if paragraph_element.text:
            text_parts.append(paragraph_element.text.strip())

        # 子要素を処理
        for child in paragraph_element:
            if child.tag == 'pause':
                # ポーズタグの処理 - Google TTSでは句読点で表現
                duration = child.get('duration', '1')
                try:
                    pause_duration = float(duration) * self.config['processing']['pause_duration_multiplier']
                    # Google TTSではポーズは「、」や「。」で表現
                    if pause_duration >= 2.0:
                        text_parts.append('。')
                    elif pause_duration >= 1.0:
                        text_parts.append('、')
                except ValueError:
                    text_parts.append('、')

            # 子要素のテキスト
            if child.text:
                text_parts.append(child.text.strip())

            # 子要素の後のテキスト
            if child.tail:
                text_parts.append(child.tail.strip())

        # テキストを結合して整理
        full_text = ''.join(text_parts)
        # 複数の空白を単一の空白に
        full_text = re.sub(r'\s+', ' ', full_text)
        # 不要な空白を除去
        full_text = re.sub(r'\s*([、。])\s*', r'\1', full_text)

        return full_text.strip()

    def create_synthesis_request(self, text: str, params: Dict) -> Tuple[texttospeech.SynthesisInput, texttospeech.VoiceSelectionParams, texttospeech.AudioConfig]:
        """
        テキストから音声合成リクエストを生成

        Args:
            text: 音声合成するテキスト
            params: 音声パラメータ

        Returns:
            音声合成リクエストのコンポーネント
        """
        input_text = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=params.get('language_code', 'ja-JP'),
            name=params.get('voice_name', 'ja-JP-Standard-D')
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=getattr(texttospeech.AudioEncoding, params.get('audio_encoding', 'LINEAR16')),
            speaking_rate=params.get('speaking_rate', 1.0),
            pitch=params.get('pitch', 0.0),
            volume_gain_db=params.get('volume_gain_db', 0.0)
        )

        return input_text, voice, audio_config

    def synthesize_speech(self, text: str, params: Dict) -> Optional[bytes]:
        """
        テキストから音声データを生成

        Args:
            text: 音声合成するテキスト
            params: 音声パラメータ

        Returns:
            音声データ（バイト列）
        """
        try:
            input_text, voice, audio_config = self.create_synthesis_request(text, params)

            response = self.tts_client.synthesize_speech(
                input=input_text,
                voice=voice,
                audio_config=audio_config
            )

            if response.audio_content:
                return response.audio_content
            else:
                self.logger.error("音声合成失敗: 音声データが返されませんでした")
                return None

        except Exception as e:
            self.logger.error(f"音声合成エラー: {e}")
            return None

    def save_query(self, query_data: Dict, output_path: str):
        """音声クエリをファイルに保存"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(query_data, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"クエリ保存: {output_path}")
        except Exception as e:
            self.logger.error(f"クエリ保存エラー: {e}")

    def save_audio(self, audio_data: bytes, output_path: str):
        """音声データをファイルに保存"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            self.logger.debug(f"音声保存: {output_path}")
        except Exception as e:
            self.logger.error(f"音声保存エラー: {e}")

    def _get_query_hash(self, text: str, params: Dict) -> str:
        """
        クエリ内容（テキスト＋パラメータ）をハッシュ化
        """
        hash_input = json.dumps({'text': text, **params}, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]

    def process_paragraph(self, paragraph: Dict, xml_basename: str) -> Tuple[bool, str]:
        """
        単一の段落を処理（クエリ生成→音声合成）

        Args:
            paragraph: 段落情報
            xml_basename: XMLファイルのベース名

        Returns:
            (成功フラグ, エラーメッセージ)
        """
        paragraph_id = paragraph['id']
        text = paragraph['text']
        params = self.tts_params
        hash_str = self._get_query_hash(text, params)

        # 出力パスを構築
        query_dir = os.path.join(self.config['processing']['queries_dir'], xml_basename)
        audio_dir = os.path.join(self.config['processing']['audio_dir'], xml_basename)

        query_path = os.path.join(query_dir, f"{paragraph_id}_{hash_str}.json")
        audio_path = os.path.join(audio_dir, f"{paragraph_id}_{hash_str}.{self.config['processing']['audio_format']}")

        # 既存ファイルがあればスキップ
        if os.path.exists(query_path) and os.path.exists(audio_path):
            self.logger.info(f"スキップ: {paragraph_id} (既存ファイルあり)")
            return True, ""

        try:
            # クエリデータを準備
            query_data = {
                'id': paragraph_id,
                'text': text,
                'params': params,
                'hash': hash_str
            }

            # クエリ保存
            self.save_query(query_data, query_path)

            # 音声合成
            audio_data = self.synthesize_speech(text, params)

            if audio_data is None:
                return False, f"音声合成失敗: {paragraph_id}"

            # 音声保存
            self.save_audio(audio_data, audio_path)

            self.logger.info(f"処理完了: {paragraph_id}")
            return True, ""

        except Exception as e:
            error_msg = f"段落処理エラー {paragraph_id}: {e}"
            self.logger.error(error_msg)
            return False, error_msg

    def process_xml_file(self, xml_path: str) -> Dict[str, int]:
        """
        XMLファイル全体を処理

        Args:
            xml_path: XMLファイルのパス

        Returns:
            処理結果の統計情報
        """
        xml_basename = os.path.splitext(os.path.basename(xml_path))[0]
        self.logger.info(f"XMLファイル処理開始: {xml_path}")

        # XMLをパース
        paragraphs, slide_transitions = self.parse_xml_script(xml_path)
        if not paragraphs:
            self.logger.warning(f"処理対象の段落が見つかりません: {xml_path}")
            return {'total': 0, 'success': 0, 'failed': 0}

        # paragraph_ids指定時はフィルタ
        if self.paragraph_ids:
            paragraphs = [p for p in paragraphs if p['id'] in self.paragraph_ids]

        # 並行処理で段落を処理
        results = {'total': len(paragraphs), 'success': 0, 'failed': 0}
        failed_paragraphs = []

        max_workers = self.config['processing']['max_concurrent_requests']

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 段落処理タスクを投入
            future_to_paragraph = {
                executor.submit(self.process_paragraph, paragraph, xml_basename): paragraph
                for paragraph in paragraphs
            }

            # 結果を収集
            for future in as_completed(future_to_paragraph):
                paragraph = future_to_paragraph[future]
                try:
                    success, error_msg = future.result()
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                        failed_paragraphs.append((paragraph['id'], error_msg))
                except Exception as e:
                    results['failed'] += 1
                    failed_paragraphs.append((paragraph['id'], str(e)))

        # 結果をレポート
        self.logger.info(f"処理完了: {xml_basename} - 成功: {results['success']}, 失敗: {results['failed']}")

        if failed_paragraphs:
            self.logger.warning("失敗した段落:")
            for paragraph_id, error_msg in failed_paragraphs:
                self.logger.warning(f"  {paragraph_id}: {error_msg}")

        return results

    def process_all_scripts(self, file_patterns: Optional[List[str]] = None) -> Dict[str, Dict[str, int]]:
        """
        スクリプトディレクトリ内のXMLファイルを処理

        Args:
            file_patterns: 処理対象のファイルパターン（指定しない場合は全て）

        Returns:
            ファイルごとの処理結果
        """
        scripts_dir = self.config['processing']['scripts_dir']

        if not os.path.exists(scripts_dir):
            self.logger.error(f"スクリプトディレクトリが見つかりません: {scripts_dir}")
            return {}

        # XMLファイルを検索
        all_xml_files = [f for f in os.listdir(scripts_dir) if f.endswith('.xml')]

        if file_patterns:
            # パターンマッチング
            xml_files = []
            for pattern in file_patterns:
                matching_files = [f for f in all_xml_files if pattern in f]
                xml_files.extend(matching_files)
            # 重複除去
            xml_files = list(set(xml_files))
        else:
            xml_files = all_xml_files

        if not xml_files:
            self.logger.warning(f"対象のXMLファイルが見つかりません: {scripts_dir}")
            return {}

        self.logger.info(f"{len(xml_files)} 個のXMLファイルを処理します: {xml_files}")

        results = {}
        for xml_file in xml_files:
            xml_path = os.path.join(scripts_dir, xml_file)
            file_results = self.process_xml_file(xml_path)
            results[xml_file] = file_results

        return results

    def create_combined_audio(self, xml_file: str, page_turn_pause: Optional[float] = None, paragraph_pause: Optional[float] = None) -> Optional[str]:
        """
        XMLファイルに基づいて結合版音声を作成

        Args:
            xml_file: XMLファイル名
            page_turn_pause: ページめくりポーズ（秒）
            paragraph_pause: パラグラフ間ポーズ（秒）

        Returns:
            作成された結合音声ファイルのパス（失敗時はNone）
        """
        scripts_dir = self.config['processing']['scripts_dir']
        audio_dir = self.config['processing']['audio_dir']
        combined_dir = self.config['processing']['combined_dir']

        # デフォルト値の設定
        page_turn_pause_val = page_turn_pause if page_turn_pause is not None else self.config['processing']['page_turn_pause']
        paragraph_pause_val = paragraph_pause if paragraph_pause is not None else self.config['processing']['paragraph_pause']

        xml_path = os.path.join(scripts_dir, xml_file)
        xml_basename = os.path.splitext(xml_file)[0]

        # XMLをパースして段落とスライド情報を取得
        paragraphs, slide_transitions = self.parse_xml_script(xml_path)
        if not paragraphs:
            self.logger.error(f"段落が見つかりません: {xml_file}")
            return None

        # ハッシュ計算用のデータを準備
        hash_data = {
            'paragraphs': [p['id'] for p in paragraphs],
            'page_turn_pause': page_turn_pause_val,
            'paragraph_pause': paragraph_pause_val,
            'audio_files': []
        }

        # 音声ファイルの存在確認とハッシュデータ収集
        audio_subdir = os.path.join(audio_dir, xml_basename)
        if not os.path.exists(audio_subdir):
            self.logger.error(f"音声ディレクトリが見つかりません: {audio_subdir}")
            return None

        audio_files = []
        for paragraph in paragraphs:
            paragraph_id = paragraph['id']
            # 該当する音声ファイルを探す（ハッシュ付きファイル名）
            matching_files = [f for f in os.listdir(audio_subdir) if f.startswith(f"{paragraph_id}_")]
            if not matching_files:
                self.logger.error(f"音声ファイルが見つかりません: {paragraph_id}")
                return None

            audio_file = matching_files[0]  # 最初の一致するファイルを使用
            audio_path = os.path.join(audio_subdir, audio_file)
            audio_files.append(audio_path)
            hash_data['audio_files'].append(audio_file)

        # 結合ファイルのハッシュを計算
        combined_hash = hashlib.sha256(
            json.dumps(hash_data, ensure_ascii=False, sort_keys=True).encode('utf-8')
        ).hexdigest()[:16]

        # 結合ファイルのパス
        os.makedirs(combined_dir, exist_ok=True)
        combined_filename = f"{xml_basename}_{combined_hash}.{self.config['processing']['audio_format']}"
        combined_path = os.path.join(combined_dir, combined_filename)

        # 既存ファイルがあればスキップ
        if os.path.exists(combined_path):
            self.logger.info(f"結合音声ファイルが既に存在します: {combined_filename}")
            return combined_path

        try:
            # 音声ファイルを結合
            self.logger.info(f"音声結合開始: {xml_basename}")
            combined_audio = AudioSegment.empty()

            slide_transition_map = {pid: (slide_num, slide_title) for pid, slide_num, slide_title in slide_transitions}

            for i, (paragraph, audio_file) in enumerate(zip(paragraphs, audio_files)):
                # 音声ファイルを読み込み
                audio_segment = AudioSegment.from_file(audio_file)
                combined_audio += audio_segment

                # パラグラフ間のポーズを追加（最後のパラグラフ以外）
                if i < len(paragraphs) - 1:
                    # 次のパラグラフでスライドが変わる場合はページめくりポーズ
                    current_slide = slide_transition_map.get(paragraph['id'])
                    next_paragraph = paragraphs[i + 1]
                    next_slide = slide_transition_map.get(next_paragraph['id'])

                    if current_slide and next_slide and current_slide[0] != next_slide[0]:
                        # ページめくりポーズ
                        pause_duration = page_turn_pause_val * 1000  # pydubはミリ秒単位
                        self.logger.debug(f"ページめくりポーズ {page_turn_pause_val}秒: {paragraph['id']} -> {next_paragraph['id']}")
                    else:
                        # 通常のパラグラフ間ポーズ
                        pause_duration = paragraph_pause_val * 1000
                        self.logger.debug(f"パラグラフ間ポーズ {paragraph_pause_val}秒: {paragraph['id']} -> {next_paragraph['id']}")

                    pause_segment = AudioSegment.silent(duration=int(pause_duration))
                    combined_audio += pause_segment

            # 結合音声を保存
            combined_audio.export(combined_path, format=self.config['processing']['audio_format'])

            duration_seconds = len(combined_audio) / 1000
            self.logger.info(f"音声結合完了: {combined_filename} (長さ: {duration_seconds:.1f}秒)")

            return combined_path

        except Exception as e:
            self.logger.error(f"音声結合エラー: {e}")
            return None


@click.group()
@click.option('--config', default='config.yaml', help='設定ファイルのパス')
@click.option('--verbose', '-v', is_flag=True, help='詳細ログを出力')
@click.option('--dry-run', is_flag=True, help='Google TTS API認証なしで構造確認のみ実行')
@click.pass_context
def cli(ctx, config, verbose, dry_run):
    """Google TTS XML Processor - XMLスクリプトから音声を生成"""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['dry_run'] = dry_run


@cli.command()
@click.option('--files', '-f', multiple=True, help='処理対象のXMLファイル（部分一致、複数指定可）')
@click.option('--paragraph-ids', '-p', multiple=True, help='処理対象の段落ID（複数指定可）')
@click.pass_context
def synthesize(ctx, files, paragraph_ids):
    """音声合成を実行"""
    config_path = ctx.obj['config_path']

    # ログレベルの設定
    if ctx.obj['verbose']:
        logging.basicConfig(level=logging.DEBUG)

    try:
        processor = GoogleTTSProcessor(
            config_path=config_path,
            paragraph_ids=list(paragraph_ids) if paragraph_ids else None
        )

        # Google TTS接続確認
        if not processor.check_google_tts_connection():
            click.echo("エラー: Google TTS APIに接続できません。", err=True)
            click.echo("認証情報（GOOGLE_APPLICATION_CREDENTIALS）が正しく設定されているか確認してください。", err=True)
            return

        click.echo("Google TTS音声合成処理を開始します...")

        # ファイル指定がある場合はそれを使用、ない場合は全ファイル
        file_patterns = list(files) if files else None
        results = processor.process_all_scripts(file_patterns)

        # 結果サマリを表示
        click.echo("\n=== 処理結果サマリ ===")
        total_files = len(results)
        total_paragraphs = sum(r['total'] for r in results.values())
        total_success = sum(r['success'] for r in results.values())
        total_failed = sum(r['failed'] for r in results.values())

        click.echo(f"処理ファイル数: {total_files}")
        click.echo(f"総段落数: {total_paragraphs}")
        click.echo(f"成功: {total_success}")
        click.echo(f"失敗: {total_failed}")

        if total_failed > 0:
            click.echo(f"\n警告: {total_failed} 個の段落の処理に失敗しました。", err=True)
            click.echo("詳細はログを確認してください。", err=True)

        click.echo("\n処理が完了しました。")

    except Exception as e:
        click.echo(f"エラー: {e}", err=True)


@cli.command()
@click.argument('xml_file')
@click.option('--page-turn-pause', '-pt', type=float, help='ページめくりポーズ（秒）')
@click.option('--paragraph-pause', '-pp', type=float, help='パラグラフ間ポーズ（秒）')
@click.pass_context
def combine(ctx, xml_file, page_turn_pause, paragraph_pause):
    """音声ファイルを結合して一つのファイルを作成"""
    config_path = ctx.obj['config_path']
    dry_run = ctx.obj['dry_run']

    # ログレベルの設定
    if ctx.obj['verbose']:
        logging.basicConfig(level=logging.DEBUG)

    try:
        if dry_run:
            click.echo("ドライランモード: 構造確認のみ実行します")

            # 設定ファイル読み込み
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            scripts_dir = config['processing']['scripts_dir']
            audio_dir = config['processing']['audio_dir']

            xml_path = os.path.join(scripts_dir, xml_file)
            xml_basename = os.path.splitext(xml_file)[0]

            # XMLファイルの存在確認
            if not os.path.exists(xml_path):
                click.echo(f"エラー: XMLファイルが見つかりません: {xml_path}", err=True)
                return

            # XMLパース
            tree = ET.parse(xml_path)
            root = tree.getroot()

            paragraphs = []
            slide_transitions = []
            current_slide_info = None

            for element in root:
                if element.tag == 'paragraph':
                    paragraph_id = element.get('id')
                    if paragraph_id:
                        paragraphs.append({'id': paragraph_id})
                        if current_slide_info:
                            slide_transitions.append((paragraph_id, current_slide_info[0], current_slide_info[1]))
                            current_slide_info = None
                elif element.tag == 'slide_transition':
                    slide_number = element.get('slide_number')
                    slide_title = element.get('slide_title', '')
                    if slide_number:
                        try:
                            current_slide_info = (int(slide_number), slide_title)
                        except ValueError:
                            pass

            # 音声ファイルの存在確認
            audio_subdir = os.path.join(audio_dir, xml_basename)
            if not os.path.exists(audio_subdir):
                click.echo(f"エラー: 音声ディレクトリが見つかりません: {audio_subdir}", err=True)
                return

            missing_files = []
            found_files = []
            for paragraph in paragraphs:
                paragraph_id = paragraph['id']
                matching_files = [f for f in os.listdir(audio_subdir) if f.startswith(f"{paragraph_id}_")]
                if matching_files:
                    found_files.append(matching_files[0])
                else:
                    missing_files.append(paragraph_id)

            click.echo(f"XMLファイル: {xml_file}")
            click.echo(f"段落数: {len(paragraphs)}")
            click.echo(f"スライド遷移数: {len(slide_transitions)}")
            click.echo(f"音声ファイル発見: {len(found_files)}")
            click.echo(f"音声ファイル不足: {len(missing_files)}")

            if missing_files:
                click.echo(f"不足ファイル: {missing_files[:5]}")  # 最初の5個のみ表示
                if len(missing_files) > 5:
                    click.echo(f"  ... 他 {len(missing_files) - 5} 個")

            # パラメータ情報
            page_turn_val = page_turn_pause if page_turn_pause is not None else config['processing']['page_turn_pause']
            paragraph_val = paragraph_pause if paragraph_pause is not None else config['processing']['paragraph_pause']

            click.echo(f"ページめくりポーズ: {page_turn_val}秒")
            click.echo(f"パラグラフ間ポーズ: {paragraph_val}秒")

            if len(found_files) == len(paragraphs):
                click.echo("✓ 全ての音声ファイルが揃っています。実際の結合処理が可能です。")
            else:
                click.echo("✗ 一部音声ファイルが不足しています。先に音声合成を実行してください。")

            return

        processor = GoogleTTSProcessor(config_path=config_path)

        click.echo(f"音声結合処理を開始します: {xml_file}")

        combined_path = processor.create_combined_audio(
            xml_file=xml_file,
            page_turn_pause=page_turn_pause,
            paragraph_pause=paragraph_pause
        )

        if combined_path:
            click.echo(f"結合完了: {combined_path}")
        else:
            click.echo("結合に失敗しました。", err=True)

    except Exception as e:
        click.echo(f"エラー: {e}", err=True)


@cli.command()
@click.option('--page-turn-pause', '-pt', type=float, help='ページめくりポーズ（秒）')
@click.option('--paragraph-pause', '-pp', type=float, help='パラグラフ間ポーズ（秒）')
@click.pass_context
def combine_all(ctx, page_turn_pause, paragraph_pause):
    """全XMLファイルの音声を結合"""
    config_path = ctx.obj['config_path']

    # ログレベルの設定
    if ctx.obj['verbose']:
        logging.basicConfig(level=logging.DEBUG)

    try:
        processor = GoogleTTSProcessor(config_path=config_path)

        # XMLファイル一覧を取得
        scripts_dir = processor.config['processing']['scripts_dir']
        xml_files = [f for f in os.listdir(scripts_dir) if f.endswith('.xml')]

        if not xml_files:
            click.echo("XMLファイルが見つかりません。", err=True)
            return

        click.echo(f"{len(xml_files)} 個のXMLファイルの音声結合処理を開始します...")

        success_count = 0
        for xml_file in xml_files:
            click.echo(f"処理中: {xml_file}")
            combined_path = processor.create_combined_audio(
                xml_file=xml_file,
                page_turn_pause=page_turn_pause,
                paragraph_pause=paragraph_pause
            )

            if combined_path:
                success_count += 1
                click.echo(f"  → 完了: {os.path.basename(combined_path)}")
            else:
                click.echo(f"  → 失敗: {xml_file}", err=True)

        click.echo(f"\n結合処理完了: {success_count}/{len(xml_files)} ファイル成功")

    except Exception as e:
        click.echo(f"エラー: {e}", err=True)


def main():
    """メイン関数（後方互換性のため）"""
    cli()


if __name__ == "__main__":
    cli()
