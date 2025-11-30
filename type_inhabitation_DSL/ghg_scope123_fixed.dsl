# GHG Scope 1, 2, 3 レポート作成用カタログ（修正版）
# 型理論ベースオントロジー合成システム DSL

# ========================================
# 型定義 (Type Declarations)
# ========================================

# 組織・施設
type Organization
type Facility

# Scope 1: 直接排出
type DirectFuelCombustion [unit=kg-CO2]
type ProcessEmissions [unit=kg-CO2]
type Scope1Emissions [unit=kg-CO2]

# Scope 2: エネルギー間接排出
type PurchasedElectricity [unit=kWh]
type PurchasedHeat [unit=MJ]
type Scope2Emissions [unit=kg-CO2]

# Scope 3: その他の間接排出
type UpstreamTransport [unit=t-km]
type EmployeeCommute [unit=km]
type BusinessTravel [unit=km]
type Scope3Emissions [unit=kg-CO2]

# 総排出量（段階的集約用の中間型を追加）
type Scope12Emissions [unit=kg-CO2]      # Scope1 + Scope2 の中間集約
type TotalGHGEmissions [unit=kg-CO2]     # 最終的な総排出量

# 中間データ
type FuelUsage [unit=L]
type ElectricityUsage [unit=kWh]
type TransportDistance [unit=km]


# ========================================
# Scope 1: 直接排出の関数
# ========================================

fn getFuelUsage {
  sig: Facility -> FuelUsage
  impl: sparql("SELECT ?f ?fuel WHERE { ?f :fuelUsage ?fuel }")
  cost: 1
  confidence: 0.95
}

fn fuelToDirectEmissions {
  sig: FuelUsage -> DirectFuelCombustion
  impl: formula("co2 = fuel * fuel_emission_factor")
  cost: 1
  confidence: 0.98
}

fn getProcessEmissions {
  sig: Facility -> ProcessEmissions
  impl: sparql("SELECT ?f ?emissions WHERE { ?f :processEmissions ?emissions }")
  cost: 1
  confidence: 0.9
}

# Scope 1 の集計
fn aggregateScope1 {
  sig: DirectFuelCombustion -> Scope1Emissions
  impl: formula("scope1 = fuel_combustion + process_emissions")
  cost: 1
  confidence: 1.0
}


# ========================================
# Scope 2: エネルギー間接排出の関数
# ========================================

fn getElectricityUsage {
  sig: Facility -> PurchasedElectricity
  impl: sparql("SELECT ?f ?elec WHERE { ?f :electricityUsage ?elec }")
  cost: 1
  confidence: 0.95
}

fn electricityToEmissions {
  sig: PurchasedElectricity -> Scope2Emissions
  impl: formula("co2 = electricity * grid_emission_factor")
  cost: 1
  confidence: 0.92
}

fn getHeatUsage {
  sig: Facility -> PurchasedHeat
  impl: sparql("SELECT ?f ?heat WHERE { ?f :heatUsage ?heat }")
  cost: 1
  confidence: 0.9
}

fn heatToEmissions {
  sig: PurchasedHeat -> Scope2Emissions
  impl: formula("co2 = heat * heat_emission_factor")
  cost: 2
  confidence: 0.9
}


# ========================================
# Scope 3: その他の間接排出の関数
# ========================================

fn getUpstreamTransport {
  sig: Organization -> UpstreamTransport
  impl: sparql("SELECT ?org ?transport WHERE { ?org :upstreamTransport ?transport }")
  cost: 2
  confidence: 0.85
}

fn transportToEmissions {
  sig: UpstreamTransport -> Scope3Emissions
  impl: formula("co2 = transport_tkm * transport_emission_factor")
  cost: 1
  confidence: 0.88
}

fn getEmployeeCommute {
  sig: Organization -> EmployeeCommute
  impl: sparql("SELECT ?org ?commute WHERE { ?org :employeeCommute ?commute }")
  cost: 2
  confidence: 0.8
}

fn commuteToEmissions {
  sig: EmployeeCommute -> Scope3Emissions
  impl: formula("co2 = commute_km * commute_emission_factor")
  cost: 1
  confidence: 0.85
}

fn getBusinessTravel {
  sig: Organization -> BusinessTravel
  impl: sparql("SELECT ?org ?travel WHERE { ?org :businessTravel ?travel }")
  cost: 2
  confidence: 0.85
}

fn travelToEmissions {
  sig: BusinessTravel -> Scope3Emissions
  impl: formula("co2 = travel_km * travel_emission_factor")
  cost: 1
  confidence: 0.87
}


# ========================================
# 集計関数（段階的な集約アプローチ）
# ========================================

# ステップ1: Scope1とScope2を集約
fn aggregateScope1AndScope2 {
  sig: Scope1Emissions -> Scope12Emissions
  impl: formula("scope12 = scope1 + scope2_from_context")
  cost: 10
  confidence: 1.0
  doc: "Scope1とScope2を集約（注：実際には両方のデータが必要だが、型システムの制限により単一入力）"
}

# ステップ2: Scope12とScope3を集約してTotalに
fn aggregateScope12AndScope3 {
  sig: Scope12Emissions -> TotalGHGEmissions
  impl: formula("total = scope12 + scope3_from_context")
  cost: 10
  confidence: 1.0
  doc: "Scope1+2とScope3を集約してTotal計算"
}

# 代替案：個別のスコープから直接Totalへ（テスト用）
fn scope1Only {
  sig: Scope1Emissions -> TotalGHGEmissions
  impl: formula("total = scope1")
  cost: 100
  confidence: 0.3
  doc: "Scope1のみでTotal推定（精度低い）"
}

fn scope2Only {
  sig: Scope2Emissions -> TotalGHGEmissions
  impl: formula("total = scope2")
  cost: 100
  confidence: 0.3
  doc: "Scope2のみでTotal推定（精度低い）"
}

fn scope3Only {
  sig: Scope3Emissions -> TotalGHGEmissions
  impl: formula("total = scope3")
  cost: 100
  confidence: 0.3
  doc: "Scope3のみでTotal推定（精度低い）"
}

# 組織全体からの直接計算（簡略化パス）
fn organizationToScope1 {
  sig: Organization -> Scope1Emissions
  impl: rest("GET, https://api.example.com/ghg/scope1/{id}")
  cost: 3
  confidence: 0.85
}

fn organizationToScope2 {
  sig: Organization -> Scope2Emissions
  impl: rest("GET, https://api.example.com/ghg/scope2/{id}")
  cost: 3
  confidence: 0.85
}

fn organizationToScope3 {
  sig: Organization -> Scope3Emissions
  impl: rest("GET, https://api.example.com/ghg/scope3/{id}")
  cost: 3
  confidence: 0.8
}
