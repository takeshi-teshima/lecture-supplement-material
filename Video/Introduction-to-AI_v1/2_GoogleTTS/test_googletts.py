#!/usr/bin/env python3
"""
Google TTS Processor のテストスクリプト

使用方法:
1. Google Cloudの認証情報が設定されていることを確認
2. python test_googletts.py を実行
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from googletts_processor import GoogleTTSProcessor


def create_test_xml():
    """テスト用のXMLファイルを作成"""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<manuscript>
  <paragraph id="test-001">
    これはテスト用の段落です。
    <pause duration="1"/>
    音声合成が正常に動作するかを確認します。
  </paragraph>

  <slide_transition slide_number="1" slide_title="テストスライド" />

  <paragraph id="test-002">
    2番目の段落です。
    <pause duration="2"/>
    異なるポーズ時間でテストしています。
    短い文章です。
  </paragraph>
</manuscript>"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
        f.write(xml_content)
        return f.name


def create_test_config():
    """テスト用の設定ファイルを作成"""
    config_content = {
        'google_tts': {
            'language_code': 'ja-JP',
            'voice_name': 'ja-JP-Standard-D',
            'speaking_rate': 1.0,
            'pitch': 0.0,
            'volume_gain_db': 0.0,
            'audio_encoding': 'LINEAR16'
        },
        'processing': {
            'scripts_dir': 'test_scripts',
            'queries_dir': 'test_queries',
            'audio_dir': 'test_audio',
            'audio_format': 'wav',
            'pause_duration_multiplier': 1.0,
            'max_concurrent_requests': 2,
            'retry_count': 3,
            'retry_delay': 1.0
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(levelname)s - %(message)s'
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        import yaml
        yaml.dump(config_content, f, default_flow_style=False, allow_unicode=True)
        return f.name


def test_connection():
    """Google TTS API接続テスト"""
    print("=== Google TTS API 接続テスト ===")

    config_path = create_test_config()
    try:
        processor = GoogleTTSProcessor(config_path=config_path)

        # 接続テスト
        if processor.check_google_tts_connection():
            print("✓ Google TTS API接続成功")
            return True
        else:
            print("✗ Google TTS API接続失敗")
            return False
    except Exception as e:
        print(f"✗ 接続テストエラー: {e}")
        return False
    finally:
        if os.path.exists(config_path):
            os.unlink(config_path)


def test_xml_parsing():
    """XMLパース機能テスト"""
    print("\n=== XMLパース機能テスト ===")

    xml_path = create_test_xml()
    config_path = create_test_config()

    try:
        processor = GoogleTTSProcessor(config_path=config_path)

        # XMLパースのテスト
        paragraphs = processor.parse_xml_script(xml_path)

        if len(paragraphs) == 2:
            print("✓ XMLパース成功")
            print(f"  段落数: {len(paragraphs)}")
            for p in paragraphs:
                print(f"  ID: {p['id']}, テキスト: {p['text'][:30]}...")
            return True
        else:
            print(f"✗ XMLパース失敗: 期待段落数=2, 実際={len(paragraphs)}")
            return False
    except Exception as e:
        print(f"✗ XMLパースエラー: {e}")
        return False
    finally:
        if os.path.exists(xml_path):
            os.unlink(xml_path)
        if os.path.exists(config_path):
            os.unlink(config_path)


def test_text_extraction():
    """テキスト抽出機能テスト"""
    print("\n=== テキスト抽出機能テスト ===")

    xml_path = create_test_xml()
    config_path = create_test_config()

    try:
        processor = GoogleTTSProcessor(config_path=config_path)
        paragraphs = processor.parse_xml_script(xml_path)

        # 最初の段落のテキストをチェック
        first_paragraph = paragraphs[0]
        expected_text = "これはテスト用の段落です。、音声合成が正常に動作するかを確認します。"

        if first_paragraph['text'] == expected_text:
            print("✓ テキスト抽出成功")
            print(f"  抽出テキスト: {first_paragraph['text']}")
            return True
        else:
            print(f"✗ テキスト抽出失敗")
            print(f"  期待値: {expected_text}")
            print(f"  実際値: {first_paragraph['text']}")
            return False
    except Exception as e:
        print(f"✗ テキスト抽出エラー: {e}")
        return False
    finally:
        if os.path.exists(xml_path):
            os.unlink(xml_path)
        if os.path.exists(config_path):
            os.unlink(config_path)


def test_synthesis_request():
    """音声合成リクエスト生成テスト"""
    print("\n=== 音声合成リクエスト生成テスト ===")

    config_path = create_test_config()

    try:
        processor = GoogleTTSProcessor(config_path=config_path)

        test_text = "テスト用のテキストです。"
        params = processor.tts_params

        input_text, voice, audio_config = processor.create_synthesis_request(test_text, params)

        if (input_text.text == test_text and
            voice.language_code == 'ja-JP' and
            voice.name == 'ja-JP-Standard-D'):
            print("✓ 音声合成リクエスト生成成功")
            print(f"  テキスト: {input_text.text}")
            print(f"  言語: {voice.language_code}")
            print(f"  音声: {voice.name}")
            return True
        else:
            print("✗ 音声合成リクエスト生成失敗")
            return False
    except Exception as e:
        print(f"✗ リクエスト生成エラー: {e}")
        return False
    finally:
        if os.path.exists(config_path):
            os.unlink(config_path)


def test_hash_generation():
    """ハッシュ生成テスト"""
    print("\n=== ハッシュ生成テスト ===")

    config_path = create_test_config()

    try:
        processor = GoogleTTSProcessor(config_path=config_path)

        text1 = "同じテキスト"
        text2 = "同じテキスト"
        text3 = "異なるテキスト"
        params = {'test': 'param'}

        hash1 = processor._get_query_hash(text1, params)
        hash2 = processor._get_query_hash(text2, params)
        hash3 = processor._get_query_hash(text3, params)

        if hash1 == hash2 and hash1 != hash3:
            print("✓ ハッシュ生成成功")
            print(f"  同一テキストハッシュ: {hash1[:8]}...")
            print(f"  異なるテキストハッシュ: {hash3[:8]}...")
            return True
        else:
            print("✗ ハッシュ生成失敗")
            return False
    except Exception as e:
        print(f"✗ ハッシュ生成エラー: {e}")
        return False
    finally:
        if os.path.exists(config_path):
            os.unlink(config_path)


def main():
    """メイン関数"""
    print("Google TTS Processor テスト開始\n")

    # 環境変数チェック
    if not os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print("警告: GOOGLE_APPLICATION_CREDENTIALS 環境変数が設定されていません")
        print("一部のテストがスキップされる可能性があります\n")

    tests = [
        ("接続テスト", test_connection),
        ("XMLパース機能", test_xml_parsing),
        ("テキスト抽出機能", test_text_extraction),
        ("音声合成リクエスト生成", test_synthesis_request),
        ("ハッシュ生成", test_hash_generation)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} でエラー: {e}")
            results.append((test_name, False))

    # 結果サマリ
    print("\n" + "="*50)
    print("テスト結果サマリ")
    print("="*50)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n成功: {passed}, 失敗: {failed}")

    if failed == 0:
        print("\n✓ すべてのテストが成功しました！")
    else:
        print(f"\n✗ {failed} 個のテストが失敗しました。")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
