# unit_converter.py
"""
単位変換システム

型の単位情報を解析し、必要に応じて自動的に単位変換関数を挿入します。
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
import re


@dataclass
class UnitInfo:
    """単位情報"""
    unit: str
    dimension: str  # エネルギー、質量、長さなど
    si_factor: float  # SI基本単位への変換係数


# 単位変換テーブル
UNIT_CONVERSIONS = {
    # エネルギー
    'J': UnitInfo('J', 'energy', 1.0),
    'kJ': UnitInfo('kJ', 'energy', 1000.0),
    'MJ': UnitInfo('MJ', 'energy', 1e6),
    'GJ': UnitInfo('GJ', 'energy', 1e9),
    'Wh': UnitInfo('Wh', 'energy', 3600.0),
    'kWh': UnitInfo('kWh', 'energy', 3.6e6),
    'MWh': UnitInfo('MWh', 'energy', 3.6e9),
    'cal': UnitInfo('cal', 'energy', 4.184),
    'kcal': UnitInfo('kcal', 'energy', 4184.0),

    # 質量
    'g': UnitInfo('g', 'mass', 0.001),
    'kg': UnitInfo('kg', 'mass', 1.0),
    't': UnitInfo('t', 'mass', 1000.0),
    'lb': UnitInfo('lb', 'mass', 0.453592),
    'oz': UnitInfo('oz', 'mass', 0.0283495),

    # 長さ
    'm': UnitInfo('m', 'length', 1.0),
    'km': UnitInfo('km', 'length', 1000.0),
    'cm': UnitInfo('cm', 'length', 0.01),
    'mm': UnitInfo('mm', 'length', 0.001),
    'ft': UnitInfo('ft', 'length', 0.3048),
    'in': UnitInfo('in', 'length', 0.0254),

    # 体積
    'L': UnitInfo('L', 'volume', 0.001),
    'mL': UnitInfo('mL', 'volume', 1e-6),
    'm3': UnitInfo('m3', 'volume', 1.0),
    'gal': UnitInfo('gal', 'volume', 0.00378541),

    # 時間
    's': UnitInfo('s', 'time', 1.0),
    'min': UnitInfo('min', 'time', 60.0),
    'h': UnitInfo('h', 'time', 3600.0),
    'day': UnitInfo('day', 'time', 86400.0),

    # 温度（特殊な処理が必要）
    'K': UnitInfo('K', 'temperature', 1.0),
    'C': UnitInfo('C', 'temperature', 1.0),  # オフセットが必要
    'F': UnitInfo('F', 'temperature', 5.0/9.0),  # オフセットが必要
}


class UnitConverter:
    """単位変換器"""

    def __init__(self):
        self.conversions = UNIT_CONVERSIONS

    def can_convert(self, from_unit: str, to_unit: str) -> bool:
        """2つの単位が変換可能かチェック"""
        if from_unit not in self.conversions or to_unit not in self.conversions:
            return False

        from_info = self.conversions[from_unit]
        to_info = self.conversions[to_unit]

        # 同じ次元でなければ変換不可
        return from_info.dimension == to_info.dimension

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """値を変換"""
        if from_unit == to_unit:
            return value

        if not self.can_convert(from_unit, to_unit):
            raise ValueError(f"Cannot convert from {from_unit} to {to_unit}")

        from_info = self.conversions[from_unit]
        to_info = self.conversions[to_unit]

        # 特殊ケース: 温度
        if from_info.dimension == 'temperature':
            return self._convert_temperature(value, from_unit, to_unit)

        # 一般的なケース: SI単位を経由
        si_value = value * from_info.si_factor
        result = si_value / to_info.si_factor

        return result

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """温度の変換（オフセット対応）"""
        # まずKelvinに変換
        if from_unit == 'K':
            kelvin = value
        elif from_unit == 'C':
            kelvin = value + 273.15
        elif from_unit == 'F':
            kelvin = (value - 32) * 5.0/9.0 + 273.15
        else:
            raise ValueError(f"Unknown temperature unit: {from_unit}")

        # 目的の単位に変換
        if to_unit == 'K':
            return kelvin
        elif to_unit == 'C':
            return kelvin - 273.15
        elif to_unit == 'F':
            return (kelvin - 273.15) * 9.0/5.0 + 32
        else:
            raise ValueError(f"Unknown temperature unit: {to_unit}")

    def get_conversion_factor(self, from_unit: str, to_unit: str) -> float:
        """変換係数を取得"""
        if from_unit == to_unit:
            return 1.0

        # テスト値で係数を計算
        test_value = 1.0
        converted = self.convert(test_value, from_unit, to_unit)
        return converted / test_value


class UnitAwareCatalog:
    """単位を考慮したカタログ"""

    def __init__(self, catalog):
        self.catalog = catalog
        self.converter = UnitConverter()

    def get_type_unit(self, type_name: str) -> Optional[str]:
        """型の単位を取得"""
        if type_name in self.catalog.types:
            type_info = self.catalog.types[type_name]
            return type_info.get('unit')
        return None

    def needs_conversion(self, from_type: str, to_type: str) -> bool:
        """型間で単位変換が必要かチェック"""
        from_unit = self.get_type_unit(from_type)
        to_unit = self.get_type_unit(to_type)

        if from_unit is None or to_unit is None:
            return False

        if from_unit == to_unit:
            return False

        return self.converter.can_convert(from_unit, to_unit)

    def create_conversion_function(self, from_type: str, to_type: str):
        """単位変換関数を動的に生成"""
        from synth_lib import Func

        from_unit = self.get_type_unit(from_type)
        to_unit = self.get_type_unit(to_type)

        if from_unit is None or to_unit is None:
            raise ValueError(f"Cannot create conversion function: missing unit info")

        factor = self.converter.get_conversion_factor(from_unit, to_unit)

        return Func(
            id=f"convert_{from_unit}_to_{to_unit}",
            dom=from_type,
            cod=to_type,
            cost=0.1,  # 単位変換は低コスト
            conf=1.0,  # 確定的な変換
            impl={
                'kind': 'unit_conversion',
                'from_unit': from_unit,
                'to_unit': to_unit,
                'factor': factor
            },
            inverse_of=None
        )

    def augment_path_with_conversions(self, path, src_type: str, goal_type: str):
        """
        パスに単位変換を自動挿入

        Args:
            path: 関数のリスト
            src_type: ソース型
            goal_type: ゴール型

        Returns:
            単位変換が挿入された新しいパス
        """
        if not path:
            return path

        augmented = []
        current_type = src_type

        for func in path:
            # 現在の型と関数のドメインが異なる単位の場合、変換を挿入
            if self.needs_conversion(current_type, func.dom):
                conv_func = self.create_conversion_function(current_type, func.dom)
                augmented.append(conv_func)
                current_type = func.dom

            # 元の関数を追加
            augmented.append(func)
            current_type = func.cod

        # 最後の型とゴール型が異なる場合、変換を挿入
        if self.needs_conversion(current_type, goal_type):
            conv_func = self.create_conversion_function(current_type, goal_type)
            augmented.append(conv_func)

        return augmented


# 使用例
if __name__ == '__main__':
    converter = UnitConverter()

    # エネルギー変換のテスト
    print("Energy conversions:")
    print(f"100 kWh = {converter.convert(100, 'kWh', 'J')} J")
    print(f"100 kWh = {converter.convert(100, 'kWh', 'MJ')} MJ")
    print(f"1000 kcal = {converter.convert(1000, 'kcal', 'kWh')} kWh")

    # 質量変換のテスト
    print("\nMass conversions:")
    print(f"1 kg = {converter.convert(1, 'kg', 'g')} g")
    print(f"1 lb = {converter.convert(1, 'lb', 'kg')} kg")

    # 温度変換のテスト
    print("\nTemperature conversions:")
    print(f"0 C = {converter.convert(0, 'C', 'K')} K")
    print(f"32 F = {converter.convert(32, 'F', 'C')} C")
    print(f"100 C = {converter.convert(100, 'C', 'F')} F")
