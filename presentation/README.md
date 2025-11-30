# プロジェクト紹介スライド

型理論ベース オントロジー探索・合成システムの紹介スライドです。

## ファイル

### index.html
**HTML5スライド（推奨）**

reveal.jsを使用したインタラクティブなスライドです。

**使い方:**
```bash
# ブラウザで開く
open index.html
# または
firefox index.html
```

**特徴:**
- レスポンシブデザイン
- コードのシンタックスハイライト
- キーボードナビゲーション（矢印キー、スペース）
- 印刷対応

**キーボードショートカット:**
- `→` / `Space`: 次のスライド
- `←`: 前のスライド
- `f`: フルスクリーン
- `s`: スピーカーノート（プレゼンターモード）
- `o`: スライド一覧
- `Esc`: スライド一覧を閉じる

### slides.pptx
**PowerPoint形式**

Microsoft PowerPoint、LibreOffice Impress、Google Slidesなどで開けます。

**使い方:**
```bash
# LibreOfficeで開く
libreoffice slides.pptx

# Windowsの場合
start slides.pptx

# macOSの場合
open slides.pptx
```

**特徴:**
- 標準的なPPTX形式
- 編集可能
- 既存のプレゼンテーションワークフローに統合可能

## スライドの構成

1. **理論的基礎**
   - Span/Cospan理論
   - 型理論・型充足問題
   - 中間型の自動発見

2. **YAMLベースの実装**
   - カタログ定義
   - 探索アルゴリズム
   - 検証結果

3. **本格的なDSL設計**
   - DSL構文
   - 実装の種類
   - 実行機能

4. **CFP計算の実例**
   - 問題設定
   - 探索プロセス
   - メトリクス分析
   - GHG Scope 1,2,3シナリオ

5. **まとめと今後の展望**
   - 主要な成果
   - 実装済み機能
   - 今後の拡張

## スライド生成スクリプト

### generate_pptx.py

PPTXファイルを再生成する場合:

```bash
python3 generate_pptx.py
```

**依存関係:**
```bash
pip install python-pptx
```

## カスタマイズ

### HTMLスライドの編集

`index.html`を直接編集してください。reveal.jsのドキュメント: https://revealjs.com/

### PPTXスライドの編集

1. PowerPointやLibreOfficeで`slides.pptx`を開いて編集
2. または`generate_pptx.py`を編集して再生成

## プレゼンテーションのヒント

### HTMLスライド
- プレゼンターモード（`s`キー）を使うと、ノートとタイマーが表示されます
- PDFにエクスポートする場合: ブラウザの印刷機能で「PDFに保存」

### PPTXスライド
- スピーカーノートはPowerPointのノート欄に追加可能
- アニメーションは含まれていませんが、PowerPointで追加できます

## トラブルシューティング

### HTMLスライドが表示されない
- インターネット接続を確認（reveal.jsがCDNから読み込まれます）
- ローカルサーバーで実行することを推奨:
  ```bash
  python3 -m http.server 8000
  # ブラウザで http://localhost:8000/index.html を開く
  ```

### PPTXファイルが開けない
- 対応するアプリケーションがインストールされているか確認
- LibreOffice Impressは無料で利用可能: https://www.libreoffice.org/

## ライセンス

このプレゼンテーションは、プロジェクト本体と同じライセンス（MIT License）で提供されます。
