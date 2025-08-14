#!/usr/bin/env python3
"""
VOICEVOX音声合成システムのテストスクリプト

VOICEVOXの接続確認と基本的な機能テストを行います。
"""

import requests
import json
import yaml
import os
from voicevox_processor import VoiceVoxProcessor


def test_voicevox_connection():
    """VOICEVOX接続テスト"""
    print("=== VOICEVOX接続テスト ===")

    try:
        response = requests.get("http://localhost:50021/version", timeout=5)
        if response.status_code == 200:
            try:
                version_info = response.json()
                if isinstance(version_info, dict) and 'version' in version_info:
                    print(f"✓ 接続成功: VOICEVOX {version_info['version']}")
                else:
                    print(f"✓ 接続成功: VOICEVOX {version_info}")
            except Exception:
                print(f"✓ 接続成功: VOICEVOX {response.text}")
            return True
        else:
            print(f"✗ 接続失敗: ステータスコード {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 接続エラー: {e}")
        return False


def test_speakers_list():
    """話者リスト取得テスト"""
    print("\n=== 話者リスト取得テスト ===")

    try:
        response = requests.get("http://localhost:50021/speakers", timeout=5)
        if response.status_code == 200:
            speakers = response.json()
            print(f"✓ 話者リスト取得成功: {len(speakers)} 人の話者")

            print("\n利用可能な話者:")
            for speaker in speakers[:5]:  # 最初の5人を表示
                speaker_name = speaker['name']
                for style in speaker['styles']:
                    style_name = style['name']
                    style_id = style['id']
                    print(f"  ID {style_id}: {speaker_name} ({style_name})")

            if len(speakers) > 5:
                print(f"  ... 他 {len(speakers) - 5} 人")

            return True
        else:
            print(f"✗ 話者リスト取得失敗: ステータスコード {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ 話者リスト取得エラー: {e}")
        return False


def test_audio_synthesis():
    """音声合成テスト"""
    print("\n=== 音声合成テスト ===")

    test_text = "こんにちは。これはテスト音声です。"
    speaker_id = 3  # ずんだもん（ノーマル）

    try:
        # 音声クエリ生成
        print(f"テキスト: {test_text}")
        print(f"話者ID: {speaker_id}")

        query_response = requests.post(
            "http://localhost:50021/audio_query",
            params={'text': test_text, 'speaker': speaker_id},
            timeout=10
        )

        if query_response.status_code != 200:
            print(f"✗ クエリ生成失敗: {query_response.status_code}")
            return False

        query = query_response.json()
        print("✓ 音声クエリ生成成功")

        # 音声合成
        synthesis_response = requests.post(
            "http://localhost:50021/synthesis",
            params={'speaker': speaker_id},
            headers={'Content-Type': 'application/json'},
            json=query,
            timeout=30
        )

        if synthesis_response.status_code != 200:
            print(f"✗ 音声合成失敗: {synthesis_response.status_code}")
            return False

        audio_data = synthesis_response.content
        audio_size = len(audio_data)
        print(f"✓ 音声合成成功: {audio_size} バイト")

        # テスト音声を保存
        test_output_path = "test_audio.wav"
        with open(test_output_path, 'wb') as f:
            f.write(audio_data)
        print(f"✓ テスト音声保存: {test_output_path}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ 音声合成エラー: {e}")
        return False


def test_config_file():
    """設定ファイルテスト"""
    print("\n=== 設定ファイルテスト ===")

    config_path = "config.yaml"

    if not os.path.exists(config_path):
        print(f"✗ 設定ファイルが見つかりません: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 必須項目の確認
        required_keys = [
            'voicevox.host',
            'voicevox.port',
            'voicevox.speaker_id',
            'processing.scripts_dir',
            'processing.queries_dir',
            'processing.audio_dir'
        ]

        missing_keys = []
        for key_path in required_keys:
            keys = key_path.split('.')
            current = config
            try:
                for key in keys:
                    current = current[key]
            except (KeyError, TypeError):
                missing_keys.append(key_path)

        if missing_keys:
            print(f"✗ 設定ファイルに不足項目: {missing_keys}")
            return False

        print("✓ 設定ファイル読み込み成功")
        print(f"  VOICEVOX: {config['voicevox']['host']}:{config['voicevox']['port']}")
        print(f"  話者ID: {config['voicevox']['speaker_id']}")
        print(f"  スクリプトディレクトリ: {config['processing']['scripts_dir']}")

        return True

    except yaml.YAMLError as e:
        print(f"✗ 設定ファイル読み込みエラー: {e}")
        return False


def test_xml_parsing():
    """XMLパースィングテスト"""
    print("\n=== XMLパースィングテスト ===")

    # テスト用XMLファイルを作成
    test_xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<manuscript>
  <paragraph id="test-001">
    こんにちは。
    <pause duration="1"/>
    これはテスト用の段落です。
  </paragraph>

  <slide_transition slide_number="1" slide_title="テストスライド" />

  <paragraph id="test-002">
    二番目の段落です。
    <pause duration="2"/>
    ポーズも含まれています。
  </paragraph>
</manuscript>'''

    test_xml_path = "test_script.xml"

    try:
        with open(test_xml_path, 'w', encoding='utf-8') as f:
            f.write(test_xml_content)

        processor = VoiceVoxProcessor()
        paragraphs = processor.parse_xml_script(test_xml_path)

        if len(paragraphs) == 2:
            print("✓ XMLパース成功")
            for i, paragraph in enumerate(paragraphs, 1):
                print(f"  段落{i}: ID={paragraph['id']}, テキスト='{paragraph['text'][:50]}...'")

            # テストファイルを削除
            os.remove(test_xml_path)
            return True
        else:
            print(f"✗ XMLパース失敗: 期待された段落数=2, 実際={len(paragraphs)}")
            return False

    except Exception as e:
        print(f"✗ XMLパースエラー: {e}")
        return False
    finally:
        if os.path.exists(test_xml_path):
            os.remove(test_xml_path)


def main():
    """メインテスト実行"""
    print("VOICEVOX音声合成システム - 動作確認テスト")
    print("=" * 50)

    tests = [
        ("VOICEVOX接続", test_voicevox_connection),
        ("話者リスト取得", test_speakers_list),
        ("設定ファイル", test_config_file),
        ("XMLパース", test_xml_parsing),
        ("音声合成", test_audio_synthesis),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}でエラー発生: {e}")
            results.append((test_name, False))

    # 結果サマリ
    print("\n" + "=" * 50)
    print("テスト結果サマリ")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\n合格: {passed}/{len(results)} テスト")

    if passed == len(results):
        print("\n🎉 すべてのテストが成功しました！システムは正常に動作します。")
    else:
        print(f"\n⚠️  {len(results) - passed} 個のテストが失敗しました。")
        print("問題を解決してから再度テストしてください。")

    # テストファイルのクリーンアップ
    test_files = ["test_audio.wav", "test_script.xml"]
    for test_file in test_files:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"テストファイルを削除: {test_file}")


if __name__ == "__main__":
    main()
