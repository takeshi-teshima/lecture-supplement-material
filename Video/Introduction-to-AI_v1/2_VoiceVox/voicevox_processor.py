#!/usr/bin/env python3
"""
XMLスクリプトからVOICEVOXを使って音声合成を行うスクリプト

使用方法:
1. VOICEVOXを起動しておく
2. config.yamlを設定する
3. python voicevox_processor.py を実行する
"""


import os
import re
import json
import time
import logging
import requests
import yaml
import hashlib
import argparse
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed


class VoiceVoxProcessor:
    """XMLスクリプトをVOICEVOXで音声合成するプロセッサ"""

    def __init__(self, config_path: str = "config.yaml", paragraph_ids: Optional[List[str]] = None):
        """
        初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        self.base_url = f"http://{self.config['voicevox']['host']}:{self.config['voicevox']['port']}"
        self.voicevox_params = self.config.get('voicevox_params', {})
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

    def check_voicevox_connection(self) -> bool:
        """VOICEVOXサーバーの接続確認"""
        try:
            response = requests.get(f"{self.base_url}/version", timeout=5)
            if response.status_code == 200:
                version_info = response.json()
                self.logger.info(f"VOICEVOX接続成功: {version_info}")
                return True
            else:
                self.logger.error(f"VOICEVOX接続失敗: ステータスコード {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"VOICEVOX接続エラー: {e}")
            return False

    def parse_xml_script(self, xml_path: str) -> List[Dict]:
        """
        XMLスクリプトをパースして段落情報を抽出

        Args:
            xml_path: XMLファイルのパス

        Returns:
            段落情報のリスト
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            paragraphs = []
            for paragraph in root.findall('paragraph'):
                paragraph_id = paragraph.get('id')
                if not paragraph_id:
                    continue

                # テキスト内容を取得（ポーズタグなどを処理）
                text = self._extract_text_content(paragraph)

                if text.strip():  # 空でないテキストのみ処理
                    paragraphs.append({
                        'id': paragraph_id,
                        'text': text,
                        'original_xml': ET.tostring(paragraph, encoding='unicode')
                    })

            self.logger.info(f"XMLファイル {xml_path} から {len(paragraphs)} 個の段落を抽出")
            return paragraphs

        except ET.ParseError as e:
            self.logger.error(f"XMLパースエラー: {e}")
            return []
        except Exception as e:
            self.logger.error(f"XMLファイル処理エラー: {e}")
            return []

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
                # ポーズタグの処理
                duration = child.get('duration', '1')
                try:
                    pause_duration = float(duration) * self.config['processing']['pause_duration_multiplier']
                    # VOICEVOXではポーズは「、」や「。」で表現
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

    def create_audio_query(self, text: str, speaker_id: int, params: Dict) -> Optional[Dict]:
        """
        テキストから音声クエリを生成

        Args:
            text: 音声合成するテキスト
            speaker_id: 話者ID

        Returns:
            音声クエリ（辞書形式）
        """
        try:
            req_params = {
                'text': text,
                'speaker': speaker_id
            }
            response = requests.post(
                f"{self.base_url}/audio_query",
                params=req_params,
                timeout=30
            )
            if response.status_code == 200:
                query = response.json()
                # 音声パラメータを設定に基づいて調整
                query['speedScale'] = params.get('speed_scale', 1.0)
                query['pitchScale'] = params.get('pitch_scale', 0.0)
                query['intonationScale'] = params.get('intonation_scale', 1.0)
                query['volumeScale'] = params.get('volume_scale', 1.0)
                return query
            else:
                self.logger.error(f"音声クエリ生成失敗: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"音声クエリ生成エラー: {e}")
            return None

    def synthesize_speech(self, query: Dict, speaker_id: int) -> Optional[bytes]:
        """
        音声クエリから音声データを生成

        Args:
            query: 音声クエリ
            speaker_id: 話者ID

        Returns:
            音声データ（バイト列）
        """
        try:
            params = {'speaker': speaker_id}
            headers = {'Content-Type': 'application/json'}

            response = requests.post(
                f"{self.base_url}/synthesis",
                params=params,
                headers=headers,
                json=query,
                timeout=60
            )

            if response.status_code == 200:
                return response.content
            else:
                self.logger.error(f"音声合成失敗: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"音声合成エラー: {e}")
            return None

    def save_query(self, query: Dict, output_path: str):
        """音声クエリをファイルに保存"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(query, f, ensure_ascii=False, indent=2)
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
        params = self.voicevox_params
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
            # 音声クエリ生成
            speaker_id = params.get('speaker_id', 1)
            query = self.create_audio_query(text, speaker_id, params)

            if query is None:
                return False, f"クエリ生成失敗: {paragraph_id}"

            # クエリ保存
            self.save_query(query, query_path)

            # 音声合成
            audio_data = self.synthesize_speech(query, speaker_id)

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
        paragraphs = self.parse_xml_script(xml_path)
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

    def process_all_scripts(self) -> Dict[str, Dict[str, int]]:
        """
        スクリプトディレクトリ内のすべてのXMLファイルを処理

        Returns:
            ファイルごとの処理結果
        """
        scripts_dir = self.config['processing']['scripts_dir']

        if not os.path.exists(scripts_dir):
            self.logger.error(f"スクリプトディレクトリが見つかりません: {scripts_dir}")
            return {}

        # XMLファイルを検索
        xml_files = [f for f in os.listdir(scripts_dir) if f.endswith('.xml')]

        if not xml_files:
            self.logger.warning(f"XMLファイルが見つかりません: {scripts_dir}")
            return {}

        self.logger.info(f"{len(xml_files)} 個のXMLファイルを処理します")

        results = {}
        for xml_file in xml_files:
            xml_path = os.path.join(scripts_dir, xml_file)
            file_results = self.process_xml_file(xml_path)
            results[xml_file] = file_results

        return results


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="VOICEVOX XML Processor")
    parser.add_argument("--paragraph-ids", nargs="*", help="再生成したい段落ID（複数可）")
    args = parser.parse_args()

    processor = VoiceVoxProcessor(paragraph_ids=args.paragraph_ids)

    # VOICEVOX接続確認
    if not processor.check_voicevox_connection():
        print("エラー: VOICEVOXサーバーに接続できません。")
        print("VOICEVOXが起動しているか確認してください。")
        return

    print("VOICEVOX音声合成処理を開始します...")

    # 全スクリプトを処理
    results = processor.process_all_scripts()

    # 結果サマリを表示
    print("\n=== 処理結果サマリ ===")
    total_files = len(results)
    total_paragraphs = sum(r['total'] for r in results.values())
    total_success = sum(r['success'] for r in results.values())
    total_failed = sum(r['failed'] for r in results.values())

    print(f"処理ファイル数: {total_files}")
    print(f"総段落数: {total_paragraphs}")
    print(f"成功: {total_success}")
    print(f"失敗: {total_failed}")

    if total_failed > 0:
        print(f"\n警告: {total_failed} 個の段落の処理に失敗しました。")
        print("詳細はログを確認してください。")

    print("\n処理が完了しました。")


if __name__ == "__main__":
    main()
