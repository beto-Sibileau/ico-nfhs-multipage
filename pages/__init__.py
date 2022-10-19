from difflib import get_close_matches
from geojson_rewind import rewind
import json
import numpy as np
import pandas as pd
import re

# %%
# geojson all
json_file = "./datasets/districts_707_india.json"
with open(json_file) as json_read:
    geo_json_dict = rewind(json.load(json_read), rfc7946=False)

# %%
# district naming
district_list = [
    dist_name["properties"]["707_dist_7"] for dist_name in geo_json_dict["features"]
]
district_series = pd.Series(district_list)
ds_df = pd.DataFrame(
    {
        "Dist": district_series.str.split(",").str[0],
        "State": district_series.str.split(",").str[1],
    }
)

# %%
# first design: do not share data between pages
# (assess performance later)
df_districts = (
    pd.read_excel(
        "./datasets/NFHS4-5 District compiled file.xlsx",
        sheet_name=0,
        dtype=str,
        skiprows=1,
    )
    .rename(columns={"Districts": "District name", "Survey round": "Round"})
    .replace(
        {
            "State": {
                "WB": "West Bengal",
                "TR": "Tripura",
                "UTTAR PRADESH": "Uttar Pradesh",
                "UTTARAKHAND": "Uttarakhand",
            },
            "District name": {
                "Tue": "Mon",
            },
        }
    )
)

# %%
# auto match data and GEO states
data_st_dt_df = df_districts.groupby(
    ["State", "District name"], sort=False, as_index=False
).size()
data_states = data_st_dt_df.State.unique()
geo_states = ds_df.State.dropna().unique()

state_match = [
    get_close_matches(st.lower(), geo_states, n=1, cutoff=0.5) for st in data_states
]
state_geo_df = pd.DataFrame(
    {"State": data_states, "State_geo": [st[0] if st else np.nan for st in state_match]}
)

# manual adjust after inspection
state_geo_df.loc[state_geo_df.State == "D & D", "State_geo"] = " Daman and Diu"
state_geo_df.loc[state_geo_df.State == "DNH", "State_geo"] = " Dadra and Nagar Haveli"

# %%
# auto match data and GEO districts
district_geo_df_list = []
for state in data_states:

    data_districts = data_st_dt_df[data_st_dt_df.State == state]["District name"]
    matched_state = state_geo_df[state_geo_df.State == state].State_geo.values[0]
    geo_districts = ds_df[ds_df.State == matched_state].Dist

    district_match = [
        get_close_matches(dt.lower(), geo_districts, n=1, cutoff=0.5)
        for dt in data_districts
    ]
    district_geo_df = pd.DataFrame(
        {
            "District name": data_districts,
            "District_geo": [st[0] if st else np.nan for st in district_match],
        }
    )
    district_geo_df["State"] = state
    district_geo_df["State_geo"] = matched_state
    district_geo_df_list.append(district_geo_df)

state_district_geo_df = pd.concat(district_geo_df_list, ignore_index=True)

# manual adjust after inspection
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "D & DNH", "District_geo"
] = "Dadra & Nagar Haveli"
print(
    "Ask RAKESH about PRESENCE of District TUE in NAGALAND - NOTE also TUENSANG appears: will be considered as MON"
)

# manual adjust after inspection for double assigned ones
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "East Godavari", "District_geo"
] = "East Godavari"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "East Khasi Hills", "District_geo"
] = "East Khasi Hills"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "East Garo Hills", "District_geo"
] = "East Garo Hills"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "Imphal East", "District_geo"
] = "Imphal East"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "East District", "District_geo"
] = "East District"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "Ranga Reddy", "District_geo"
] = "Ranga Reddy"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "East Kameng", "District_geo"
] = "East Kameng"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "East Siang", "District_geo"
] = "East Siang"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "East", "District_geo"
] = "East"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "North East", "District_geo"
] = "North East"
state_district_geo_df.loc[
    state_district_geo_df["District name"] == "South East", "District_geo"
] = "South East"

# re-name for geojson: join Distric and Stae geo's
state_district_geo_df.loc[:, "District_geo"] = (
    state_district_geo_df[["District_geo", "State_geo"]]
    .fillna("N/A")
    .agg(",".join, axis=1)
)
# drop state_geo after join no longer needed
state_district_geo_df.drop(columns="State_geo", inplace=True)

# %%
# df for district map with added column for geo_json
district_map_df = df_districts.melt(
    id_vars=["State", "District name", "Round", "year"]
).merge(
    state_district_geo_df,
    on=["State", "District name"],
    how="left",
    sort=False,
)

filter_na = district_map_df.value.isnull()
filter_non_num = pd.to_numeric(district_map_df.value, errors="coerce").isnull()
# negatives detected
print(
    f"Ask RAKESH about PRESENCE of NON-NUMERICS in {(filter_non_num & ~filter_na).sum()} number of entries"
)
print(district_map_df[filter_non_num & ~filter_na].values)
# drop non-num
district_map_df = (
    district_map_df.drop(district_map_df[filter_non_num & ~filter_na].index)
    .astype({"value": "float64"})
    .reset_index(drop=True)
)

filter_negative = district_map_df.value < 0
# negatives detected
print(
    f"Ask RAKESH about PRESENCE of NEGATIVES in {(filter_negative).sum()} number of entries"
)
print(district_map_df[filter_negative].values)
# drop negatives
district_map_df = district_map_df.drop(
    district_map_df[filter_negative].index
).reset_index(drop=True)

# %%
# filter geojson by state
geo_dict = {}
for state in data_states:
    matched_state = state_geo_df[state_geo_df.State == state].State_geo.values[0]
    featured_list = [
        feature
        for feature in geo_json_dict["features"]
        if matched_state in feature["properties"]["707_dist_7"]
    ]
    geo_dict[state] = featured_list

# %%
# filter available district geo's
district_geo_dict = {}
for state in data_states:
    featured_df = state_district_geo_df.query("State == @state").reset_index(drop=True)
    district_geo_dict[state] = featured_df
district_geo_dict["All India"] = state_district_geo_df

# %%
# all states or India list --> populate dropdown later at callback
state_options = [
    {"label": l, "value": l} for l in sorted(["All India", *data_states], key=str.lower)
]

# %%
# district map indicators list
district_kpi_map = df_districts.columns[4:].values
district_map_options = [
    {"label": l, "value": l} for l in sorted(district_kpi_map, key=str.lower)
]

# read indicators domain from file
ind_domains = (
    pd.Series(
        pd.read_excel(
            "./datasets/NFHS4-5 District compiled file.xlsx", sheet_name=0, nrows=0
        )
        .columns[4:]
        .values
    ).apply(lambda x: re.split("\.|\:", x)[0])
    # .str.replace("(?i)(women)", "Female", regex=True)
)

# match domain/indicator (in theory should the same for districts and states, TBC)
nfhs_dist_ind_df = pd.DataFrame(
    {"ind_domain": ind_domains, "district_kpi": district_kpi_map}
)

# %%

# dictionary for plotly: label with no figure
label_no_fig = {
    "layout": {
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "annotations": [
            {
                "text": "No matching data",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 28},
            }
        ],
    }
}

# %%
# Data read 2: compiled india xls
df_india = pd.read_excel(
    "./datasets/NFHS- 5 compiled factsheet for INDIA.xlsx", sheet_name=0, dtype=str
)
# transform column names
df_india.rename(
    columns={
        "Sl.No": "No.",
        "NFHS-5 (2019-21)": "Urban",
        "Unnamed: 4": "Rural",
        "Unnamed: 5": "Total",
        "Unnamed: 7": "Indicator Type",
        "Unnamed: 8": "Gender",
        "Unnamed: 9": "NFHS",
        "Unnamed: 10": "Year (give as a period)",
    },
    inplace=True,
)

# add India as state column (to include in states data)
df_india["State"] = "India"
# drop first row
df_india.drop(0, inplace=True)

# concat column NFHS-4 as new rows with total only
df_india_45 = (
    pd.concat(
        [
            df_india[
                ["Indicator", "NFHS-4 (2015-16)", "Indicator Type", "Gender", "State"]
            ].rename(columns={"NFHS-4 (2015-16)": "Total"}),
            df_india.drop(columns="NFHS-4 (2015-16)"),
        ],
        ignore_index=True,
    ).fillna({"NFHS": "NFHS 4", "Year (give as a period)": "2016"})
    # drop duplicates if missing gender specification
    .drop_duplicates(
        subset=["Indicator Type", "Indicator", "Gender", "NFHS"],
        keep=False,
        ignore_index=True,
    )
    # replace gender values
    # .replace(
    #     {"Gender": {"(?i)(female)": "Female", r"(?i)(\bmale\b)": "Men"}}, regex=True
    # )
)

# %%
# Data read 3: compiled states xls
df_states = (
    pd.read_excel("./datasets/NFHS345.xlsx", sheet_name=0, dtype=str)
    # drop duplicates if missing gender specification
    # .drop_duplicates(
    #     subset=["Indicator Type", "Indicator", "State", "Gender", "NFHS"],
    #     keep=False,
    #     ignore_index=True,
    # )
    # replace gender values
    # .replace(
    #     {"Gender": {"(?i)(female)": "Female", r"(?i)(\bmale\b)": "Male"}}, regex=True
    # )
)

# print for Rakesh missing gender entries
mask_state_dup = df_states[
    df_states.duplicated(
        subset=["Indicator Type", "Indicator", "State", "Gender", "NFHS"],
        keep=False,
    )
]
print(f"RAKESH - missing gender in {len(mask_state_dup)} rows in states data:")
print(mask_state_dup.values)

# now drop duplicates in missing gender specification - inplace
df_states.drop_duplicates(
    subset=["Indicator Type", "Indicator", "State", "Gender", "NFHS"],
    keep=False,
    inplace=True,
    ignore_index=True,
)

# now replace gender values - inplace
df_states.replace(
    {"Gender": {"(?i)(female)": "Female", r"(?i)(\bmale\b)": "Male"}},
    regex=True,
    inplace=True,
)


# %%
# trend analysis (gender will be treated as a separated Type - like reported in Districts)
df_nfhs_345 = (
    pd.concat(
        [
            df_states,
            df_india_45,
        ],
        ignore_index=True,
    ).replace({"State": {r"(?i)(\bindia\b)": "All India"}}, regex=True)
    # drop duplicates: if India reported in states and separated sheet
    .drop_duplicates(
        subset=["Indicator Type", "Indicator", "State", "Gender", "NFHS"],
        keep="first",
        ignore_index=True,
    )
)

# enhance Indicator Type with Gender to avoid duplicated Indicator names
df_nfhs_345.loc[df_nfhs_345.Gender.notna(), "Indicator Type"] = df_nfhs_345[
    df_nfhs_345.Gender.notna()
][["Indicator Type", "Gender"]].agg(" - ".join, axis=1)

# retain Indicator Types - Indicator combinations
nfhs_345_ind_df = df_nfhs_345.groupby(
    ["Indicator Type", "Indicator"], sort=False, as_index=False
).size()

# states or india: nfhs_345 list
nfhs_345_states = sorted(df_nfhs_345.State.unique(), key=str.lower)

# %%
# match indicator domains reported in state vs district
# ind_dom_match = [
#     get_close_matches(
#         dmn.lower(),
#         nfhs_345_ind_df["Indicator Type"].str.lower().unique(),
#         n=1,
#         cutoff=0.6,
#     )
#     for dmn in nfhs_dist_ind_df.ind_domain.unique()
# ]

dom_in_state = [
    "Population and Household Profile",
    "Characteristics of Adults (age 15-49 years)",
    "Marriage and Fertility",
    "Current Use of Family Planning Methods (currently married women age 15–49 years)",
    "Unmet Need for Family Planning (currently married women age 15–49 years)",
    "Quality of Family Planning Services",
    "Maternity Care (for last birth in the 5 years before the survey)",
    "Delivery Care (for births in the 5 years before the survey)",
    "Child Vaccinations and Vitamin A Supplementation",
    "Treatment of Childhood Diseases (children under age 5 years)",
    "Child Feeding Practices and Nutritional Status of Children",
    "Nutritional Status of Adults (age 15-49 years)",
    "Anaemia among Children and Adults",
    "Blood Sugar Level among Adults (age 15-49 years) - Female",
    "Blood Sugar Level among Adults (age 15-49 years) - Male",
    "Hypertension among Adults (age 15 years and above) - Female",
    "Hypertension among Adults (age 15 years and above) - Male",
    "Screening for Cancer among Adults (age 30-49 years) - Female",
    "Tobacco Use and Alcohol Consumption among Adults (age 15 years and above)",
]

ind_dom_dist_state_df = pd.DataFrame(
    {
        "Dom_in_Dist": nfhs_dist_ind_df.ind_domain.unique(),
        "Dom_in_State": dom_in_state,
    }
)

# dropdown options for district indicators domain
ind_dom_dist_options = [
    {"label": l, "value": l} for l in nfhs_dist_ind_df.ind_domain.unique()
]

# %%
# match indicators within domains reported in state vs district
kpi_matched_df_list = []
for dmn in nfhs_dist_ind_df.ind_domain.unique():

    dmn_in_state = ind_dom_dist_state_df.query(
        "Dom_in_Dist == @dmn"
    ).Dom_in_State.values[0]
    ind_in_dist = nfhs_dist_ind_df.query("ind_domain == @dmn").district_kpi.values
    ind_in_state = nfhs_345_ind_df.query(
        "`Indicator Type` == @dmn_in_state"
    ).Indicator.values

    kpi_match = [
        get_close_matches(kpi, ind_in_state, n=1, cutoff=0.5) for kpi in ind_in_dist
    ]
    kpi_matched_df = pd.DataFrame(
        {
            "Dom_in_Dist": dmn,
            "Dom_in_State": dmn_in_state,
            "kpi_district": ind_in_dist,
            "kpi_state": [kpi[0] if kpi else np.nan for kpi in kpi_match],
        }
    )
    kpi_matched_df_list.append(kpi_matched_df)

dist_state_kpi_df = pd.concat(kpi_matched_df_list, ignore_index=True)
# manual adjust after inspection
dist_state_kpi_df.loc[
    dist_state_kpi_df.kpi_district == "Households surveyed", "kpi_state"
] = np.nan
dist_state_kpi_df.loc[
    dist_state_kpi_df.kpi_district
    == "49. Children age 12-23 months fully vaccinated based on information from either vaccination card or mother's recall11 (%)",
    "kpi_state",
] = np.nan
dist_state_kpi_df.loc[
    dist_state_kpi_df.kpi_district
    == "58. Children age 9-35 months who received a vitamin A dose in the last 6 months (%)",
    "kpi_state",
] = np.nan
dist_state_kpi_df.loc[
    dist_state_kpi_df.kpi_district
    == "88. Blood sugar level - high or very high (>140 mg/dl) or taking medicine to control blood sugar level23 (%)",
    "kpi_state",
] = "Blood sugar level - high (>140 mg/dl) (%)"
dist_state_kpi_df.loc[
    dist_state_kpi_df.kpi_district
    == "91. Blood sugar level - high or very high (>140 mg/dl) or taking medicine to control blood sugar level23 (%)",
    "kpi_state",
] = "Blood sugar level - high (>140 mg/dl) (%)"
dist_state_kpi_df.loc[
    dist_state_kpi_df.kpi_district
    == "101. Women age 15 years and above who use any kind of tobacco (%)",
    "kpi_state",
] = "Women who use any kind of tobacco (%)"


# %%
# filter uncleaned data in numerical columns
num_cols = ["Urban", "Rural", "Total"]
for col in num_cols:
    filter_na_345 = df_nfhs_345[col].isnull()
    filter_non_num_345 = pd.to_numeric(df_nfhs_345[col], errors="coerce").isnull()
    # non numerics
    print("Ask RAKESH about PRESENCE of NON-NUMERICS")
    print(df_nfhs_345[filter_non_num_345 & ~filter_na_345][col].values)
    # drop non-num
    df_nfhs_345 = (
        df_nfhs_345.drop(df_nfhs_345[filter_non_num_345 & ~filter_na_345].index)
        .astype({col: "float64"})
        .reset_index(drop=True)
    )

    # negatives detected
    filter_neg_345 = df_nfhs_345[col] < 0
    print("Ask RAKESH about PRESENCE of NEGATIVES")
    print(
        f"No negatives for df column {col}"
        if df_nfhs_345[filter_neg_345].empty
        else df_nfhs_345[filter_neg_345].values
    )
    # drop negatives
    df_nfhs_345 = df_nfhs_345.drop(df_nfhs_345[filter_neg_345].index).reset_index(
        drop=True
    )

# %%
# state names district/state data missmatches
district_state_match = {
    "Andaman & Nicobar": "Andaman & Nicobar Islands",
    "DNH": "Dadra & Nagar Haveli",
    "Maharastra": "Maharashtra",
    "NCT of Delhi": "Delhi",
}

# %%
# first design: do not share data between pages
# (assess performance later)
equity_df = pd.read_excel(
    "./datasets/Equity_Analysis.xlsx", sheet_name=None, dtype=str, header=2
)

# %%
# equity xls: concat excel sheets per added indicator
df_list_equity = []
for name in list(equity_df.keys())[:6]:
    equity_df[name]["Indicator"] = name
    df_list_equity.append(
        equity_df[name]
        .rename(
            columns={
                "Unnamed: 0": "State",
                "Unnamed: 1": "Total",
            }
        )
        .dropna(subset=["State", "Year"])
    )

df_equity = (
    pd.concat(df_list_equity, ignore_index=True)
    .replace(
        {
            "Indicator": {"Protected against neonatTetnus ": "Neonatal Protection"},
            "Year": {
                "2015-16": "NFHS-4 (2015-16)",
                "2019-21": "NFHS-5 (2019-21)",
                "2019-2021": "NFHS-5 (2019-21)",
            },
            "State": {
                "India": "All India",
                "Jammu And Kashmir": "Jammu and Kashmir",
                "Andaman And Nicobar Islands": "Andaman and Nicobar Islands",
                "Andaman & Nicobar Isl": "Andaman and Nicobar Islands",
                "Dadra & Nagar Haveli": "Dadra and Nagar Haveli",
                "Delhi": "Nct of Delhi",
                "Nct Of Delhi": "Nct of Delhi",
            },
        }
    )
    .astype(
        {
            "Total": "float64",
            "Rural": "float64",
            "Urban": "float64",
            "Poorest": "float64",
            "Poor": "float64",
            "Middle": "float64",
            "Rich": "float64",
            "Richest": "float64",
            "No education": "float64",
            "Primary education": "float64",
            "Secondary education": "float64",
            "Higher education": "float64",
            "SC": "float64",
            "ST": "float64",
            "OBC": "float64",
            "Others": "float64",
            "Hindu": "float64",
            "Muslim": "float64",
            "Other": "float64",
        }
    )
)
