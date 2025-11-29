# dsl_parser.py
"""
型理論ベースオントロジー合成システム用DSLパーサー

DSL構文:
  type Product
  type Energy [unit=J, range=>=0]

  fn usesEnergy {
    sig: Product -> Energy
    impl: sparql("SELECT ?p ?e WHERE { ?p :usesEnergy ?e }")
    cost: 1
    confidence: 0.9
  }
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import yaml

@dataclass
class TypeDecl:
    """型宣言"""
    name: str
    attributes: Dict[str, str] = field(default_factory=dict)

    def to_dict(self):
        """YAML形式の辞書に変換"""
        result = {'name': self.name}
        result.update(self.attributes)
        return result

@dataclass
class FunctionDecl:
    """関数宣言"""
    id: str
    sig: str
    impl: Dict[str, Any]
    cost: float = 1.0
    confidence: float = 1.0
    inverse_of: Optional[str] = None

    def to_dict(self):
        """YAML形式の辞書に変換"""
        result = {
            'id': self.id,
            'sig': self.sig,
            'impl': self.impl,
            'cost': self.cost,
            'confidence': self.confidence
        }
        if self.inverse_of:
            result['inverse_of'] = self.inverse_of
        return result

class DSLParser:
    """DSLパーサー"""

    def __init__(self):
        self.types: List[TypeDecl] = []
        self.functions: List[FunctionDecl] = []

    def parse(self, content: str):
        """DSLファイルの内容をパース"""
        self.types = []
        self.functions = []

        # コメント除去
        lines = []
        for line in content.split('\n'):
            # # 以降をコメントとして除去
            line = re.sub(r'#.*$', '', line)
            lines.append(line)
        content = '\n'.join(lines)

        # 型宣言のパース
        type_pattern = r'type\s+(\w+)(?:\s*\[([^\]]+)\])?'
        for match in re.finditer(type_pattern, content):
            name = match.group(1)
            attrs_str = match.group(2)
            attrs = {}

            if attrs_str:
                # 属性をパース
                for attr in attrs_str.split(','):
                    attr = attr.strip()
                    if '=' in attr:
                        key, value = attr.split('=', 1)
                        attrs[key.strip()] = value.strip()

            self.types.append(TypeDecl(name, attrs))

        # 関数宣言のパース（ネストした括弧に対応）
        # 手動で関数宣言を抽出
        fn_starts = [(m.start(), m.group(1)) for m in re.finditer(r'fn\s+(\w+)\s*\{', content)]

        for i, (start, fn_id) in enumerate(fn_starts):
            # 対応する閉じ括弧を見つける
            brace_count = 0
            in_string = False
            string_char = None
            body_start = content.index('{', start) + 1

            for j in range(body_start, len(content)):
                char = content[j]

                # 文字列リテラル内かどうかチェック
                if char in ('"', "'") and (j == 0 or content[j-1] != '\\'):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None

                # 文字列外の括弧のみカウント
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        if brace_count == 0:
                            # 対応する閉じ括弧を見つけた
                            fn_body = content[body_start:j]
                            fn_data = self._parse_function_body(fn_id, fn_body)
                            if fn_data:
                                self.functions.append(fn_data)
                            break
                        else:
                            brace_count -= 1

    def _parse_function_body(self, fn_id: str, body: str) -> Optional[FunctionDecl]:
        """関数本体をパース"""
        sig = None
        impl = {}
        cost = 1.0
        confidence = 1.0
        inverse_of = None

        # sig: の抽出
        sig_match = re.search(r'sig:\s*([^\n]+)', body)
        if sig_match:
            sig = sig_match.group(1).strip()
        else:
            return None

        # impl: の抽出（文字列リテラル内の括弧も考慮）
        # まず文字列リテラルを探す
        impl_match = re.search(r'impl:\s*(\w+)\s*\(\s*"([^"]+)"\s*\)', body)
        if not impl_match:
            impl_match = re.search(r"impl:\s*(\w+)\s*\(\s*'([^']+)'\s*\)", body)

        if impl_match:
            impl_kind = impl_match.group(1)
            impl_value = impl_match.group(2).strip()

            if impl_kind == 'sparql':
                impl = {'kind': 'sparql', 'query': impl_value}
            elif impl_kind == 'rest':
                # REST呼び出しの場合、メソッドとURLをパース
                parts = [p.strip().strip('"\'') for p in impl_value.split(',')]
                if len(parts) >= 2:
                    impl = {'kind': 'rest', 'method': parts[0], 'url': parts[1]}
                else:
                    impl = {'kind': 'rest', 'url': impl_value}
            elif impl_kind == 'formula':
                impl = {'kind': 'formula', 'expr': impl_value}
            else:
                impl = {'kind': impl_kind, 'value': impl_value}

        # cost: の抽出
        cost_match = re.search(r'cost:\s*([\d.]+)', body)
        if cost_match:
            cost = float(cost_match.group(1))

        # confidence: の抽出
        conf_match = re.search(r'confidence:\s*([\d.]+)', body)
        if conf_match:
            confidence = float(conf_match.group(1))

        # inverse_of: の抽出
        inv_match = re.search(r'inverse_of:\s*(\w+)', body)
        if inv_match:
            inverse_of = inv_match.group(1)

        return FunctionDecl(fn_id, sig, impl, cost, confidence, inverse_of)

    def to_catalog_dict(self) -> Dict[str, Any]:
        """カタログ辞書形式に変換（YAMLとして保存可能）"""
        return {
            'types': [t.to_dict() for t in self.types],
            'functions': [f.to_dict() for f in self.functions]
        }

    def to_yaml(self) -> str:
        """YAML文字列に変換"""
        return yaml.dump(self.to_catalog_dict(),
                        default_flow_style=False,
                        allow_unicode=True,
                        sort_keys=False)

def parse_dsl_file(filepath: str) -> Dict[str, Any]:
    """DSLファイルをパースしてカタログ辞書を返す"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = DSLParser()
    parser.parse(content)
    return parser.to_catalog_dict()

def parse_dsl_string(content: str) -> Dict[str, Any]:
    """DSL文字列をパースしてカタログ辞書を返す"""
    parser = DSLParser()
    parser.parse(content)
    return parser.to_catalog_dict()

# コマンドライン使用のための関数
def convert_dsl_to_yaml(dsl_file: str, yaml_file: str):
    """DSLファイルをYAMLに変換"""
    with open(dsl_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = DSLParser()
    parser.parse(content)

    with open(yaml_file, 'w', encoding='utf-8') as f:
        f.write(parser.to_yaml())

    print(f"Converted {dsl_file} -> {yaml_file}")
    print(f"  Types: {len(parser.types)}")
    print(f"  Functions: {len(parser.functions)}")

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python dsl_parser.py <input.dsl> [output.yaml]")
        print("  If output.yaml is not specified, prints to stdout")
        sys.exit(1)

    dsl_file = sys.argv[1]

    with open(dsl_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = DSLParser()
    parser.parse(content)

    if len(sys.argv) >= 3:
        yaml_file = sys.argv[2]
        with open(yaml_file, 'w', encoding='utf-8') as f:
            f.write(parser.to_yaml())
        print(f"Converted {dsl_file} -> {yaml_file}")
    else:
        print(parser.to_yaml())

    print(f"\n# Parsed: {len(parser.types)} types, {len(parser.functions)} functions", file=sys.stderr)
