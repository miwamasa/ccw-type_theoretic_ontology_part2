# GHG Scope 1, 2, 3 レポート作成用カタログ
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

# 総排出量
type TotalGHGEmissions [unit=kg-CO2]

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
# 集計関数（複数のScopeを統合）
# ========================================

fn aggregateScope1toTotal {
  sig: Scope1Emissions -> TotalGHGEmissions
  impl: formula("total = scope1")
  cost: 0.5
  confidence: 1.0
}

fn aggregateScope2toTotal {
  sig: Scope2Emissions -> TotalGHGEmissions
  impl: formula("total = scope2")
  cost: 0.5
  confidence: 1.0
}

fn aggregateScope3toTotal {
  sig: Scope3Emissions -> TotalGHGEmissions
  impl: formula("total = scope3")
  cost: 0.5
  confidence: 1.0
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

# 最終集計（全Scopeの合計）
fn aggregateAllScopes {
  sig: TotalGHGEmissions -> TotalGHGEmissions
  impl: formula("total = scope1 + scope2 + scope3")
  cost: 1
  confidence: 1.0
}
