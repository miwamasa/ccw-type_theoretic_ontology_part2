# Product型インタラクティブデモ

## 概要

Product型の動作を**視覚的に説明**するインタラクティブなデモです。

Scratch風のブロックビジュアルで、型合成のプロセスをアニメーション表示します。

## デモの内容

### 🎬 デモ1: 単一Scopeアプローチ（従来の問題）

**問題点を視覚化:**
- Facility → TotalGHGEmissions のパス探索
- **Scope2だけが選ばれる**問題を実演
- 結果が不正確（1500.0 kg-CO2）

**学べること:**
- 型充足アルゴリズムの動作
- コスト最小パスが常に正しいとは限らない
- 集約関数の問題

### 🎯 デモ2: Product型アプローチ（解決策）

**Product型による解決を視覚化:**
- 3つのScope（Scope1, Scope2, Scope3）を個別に計算
- Product型 `AllScopesEmissions` を構築
- 正確な総排出量を計算（3300.0 kg-CO2）

**学べること:**
- Product型の構造
- タプルとしての表現
- 全Scopeの統合方法

### ⚡ デモ3: 実行と集約（詳細プロセス）

**実行プロセスを段階的に視覚化:**
1. **入力**: Facility データ
2. **パス実行**: 各Scopeへの変換
3. **Product型構築**: タプルの作成
4. **変数バインディング**: scope1, scope2, scope3
5. **Formula実行**: `total = scope1 + scope2 + scope3`
6. **結果**: 3300.0 kg-CO2

**学べること:**
- 実行エンジンの動作
- Formula式での変数バインディング
- Product型の実用的な使い方

## 使い方

### ブラウザで開く

```bash
# Firefoxの場合
firefox demo/product_type_demo.html

# Chromeの場合
google-chrome demo/product_type_demo.html

# macOSの場合
open demo/product_type_demo.html

# または、ローカルサーバーで実行（推奨）
cd demo
python3 -m http.server 8000
# ブラウザで http://localhost:8000/product_type_demo.html を開く
```

### 操作方法

1. **デモを選択**: 左側のボタンをクリック
2. **アニメーションを観察**: 中央のキャンバスでブロックが動く様子を観察
3. **ログを確認**: 下部のログパネルで詳細を確認
4. **統計を確認**: 左側の統計パネルでパス長、コスト、信頼度、結果を確認
5. **リセット**: 🔄 リセットボタンで初期状態に戻る

## デザイン要素

### ブロックの色

| 色 | 意味 | 例 |
|----|------|-----|
| 🟢 緑 | 入力型 | Facility |
| 🔵 青 | Scope型 | Scope1Emissions, Scope2Emissions, Scope3Emissions |
| 🟠 オレンジ | Product型 | AllScopesEmissions |
| 🟣 紫 | 出力型 | TotalGHGEmissions |

### アニメーション効果

- **パルス**: 重要なブロックをハイライト
- **グロー**: 実行中の関数
- **フロー**: データの流れを示す矢印のアニメーション
- **スケール**: ホバー時の拡大効果

### ログパネル

- 🔵 **info**: 一般的な情報
- 🟢 **success**: 成功メッセージ
- 🟡 **warning**: 警告メッセージ

## 技術的な詳細

### 使用技術

- **HTML5**: 構造
- **CSS3**: スタイリング、アニメーション
- **JavaScript**: インタラクション、アニメーション制御
- **SVG**: 矢印の描画

### 特徴

- ✅ **レスポンシブ**: 様々な画面サイズに対応
- ✅ **アニメーション**: スムーズなトランジション
- ✅ **インタラクティブ**: リアルタイムのフィードバック
- ✅ **わかりやすい**: Scratch風のビジュアル表現
- ✅ **教育的**: ステップバイステップの説明

## カスタマイズ

### デモの追加

`demo` オブジェクトに新しいメソッドを追加：

```javascript
async runDemo4() {
    this.reset();
    this.addLog('デモ4開始: カスタムデモ', 'info');

    // ブロックの作成
    const block = this.createTypeBlock('MyType', 100, 100, 'type-input');

    // 矢印の作成
    const arrow = this.createArrow(200, 120, 300, 120);

    // 値の表示
    this.createValueDisplay('100.0', 100, 170);

    // ログの追加
    this.addLog('カスタム処理完了', 'success');
}
```

### スタイルの変更

CSS変数を使ってカラースキームを変更：

```css
:root {
    --primary-color: #667eea;
    --success-color: #4CAF50;
    --warning-color: #f39c12;
}
```

## トラブルシューティング

### アニメーションが表示されない

- JavaScriptが有効になっているか確認
- ブラウザのコンソールでエラーを確認
- ページをリロード

### ブロックが重なる

- ブラウザウィンドウのサイズを変更
- ズームレベルを100%に設定

### ログが表示されない

- `demo.addLog()` が正しく呼ばれているか確認
- ブラウザのコンソールでエラーを確認

## 今後の拡張案

### 追加予定の機能

1. **ドラッグ＆ドロップ**: ブロックを手動で配置
2. **カスタムDSL入力**: ユーザーが独自のDSLを入力
3. **パス探索の可視化**: Dijkstraアルゴリズムの動作を表示
4. **複数パスの比較**: 異なるパスを並べて比較
5. **エクスポート機能**: アニメーションをGIF/動画として保存

### コミュニティへの貢献

新しいデモやビジュアル改善のアイデアがあれば、ぜひPull Requestをお送りください！

## ライセンス

このデモは、プロジェクト本体と同じライセンス（MIT License）で提供されます。

## 関連ドキュメント

- [Product型ガイド](../doc/product_type_guide.md)
- [実装コスト分析](../doc/multiarg_implementation_cost_analysis.md)
- [GHG集約問題の分析](../type_inhabitation_DSL/README_GHG_AGGREGATION_ISSUE.md)
