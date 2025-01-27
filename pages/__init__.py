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
            # strip commas from district names: Hyderabad particularity
            # also noted Mahabubnagar written in two distinct forms
            # also noted Alidabad instead of Adilabad
            "District name": {
                "Tue": "Mon",
                r"\,": "",
                "Mahbubnagar": "Mahabubnagar",
                "Alidabad": "Adilabad",
            },
        },
        regex=True,
    )
)

# %%
# auto match data and GEO states
data_st_dt_df = df_districts.groupby(
    ["State", "District name"], sort=False, as_index=False
).size()
data_st_dt_df["State, District"] = data_st_dt_df[["State", "District name"]].agg(
    ",".join, axis=1
)
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

# prepare file to print-out and deliver to Rakesh
list_msg_out = []
list_msg_out.append("NFHS4-5 District compiled file.xlsx")
list_msg_out.append(
    f"Ask RAKESH about PRESENCE of NON-NUMERICS in {(filter_non_num & ~filter_na).sum()} number of entries:"
)
list_msg_out.append(", ".join(district_map_df.columns[:-1]))
for idx, a_row in district_map_df[filter_non_num & ~filter_na].iterrows():
    list_msg_out.append(", ".join(a_row.values[:-1].astype(str)))

list_msg_out.append(
    f"RAKESH - PRESENCE of NULLS in {filter_na.sum()} number of entries:"
)
for idx, a_row in district_map_df[filter_na].iterrows():
    list_msg_out.append(", ".join(a_row.values[:-1].astype(str)))

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
# take negatives in absolute value
district_map_df.loc[district_map_df.value < 0, "value"] = district_map_df[
    district_map_df.value < 0
].value.abs()

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
    {"label": l, "value": l}
    for l in [
        "All India",
        "All India Aspirational",
        "All India Gavi",
        "All India LaQshya",
        *sorted(data_states, key=str.lower),
    ]
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

# concat column NFHS-4 as new rows with total only - DO NOT ingest (Rakesh requested)
# df_india_45 = (
#     pd.concat(
#         [
#             df_india[
#                 ["Indicator", "NFHS-4 (2015-16)", "Indicator Type", "Gender", "State"]
#             ].rename(columns={"NFHS-4 (2015-16)": "Total"}),
#             df_india.drop(columns="NFHS-4 (2015-16)"),
#         ],
#         ignore_index=True,
#     ).fillna({"NFHS": "NFHS 4", "Year (give as a period)": "2016"})
#     # drop duplicates if missing gender specification
#     .drop_duplicates(
#         subset=["Indicator Type", "Indicator", "Gender", "NFHS"],
#         keep=False,
#         ignore_index=True,
#     )
# replace gender values
# .replace(
#     {"Gender": {"(?i)(female)": "Female", r"(?i)(\bmale\b)": "Men"}}, regex=True
# )
# )

# %%
# Data read 3: compiled states xls
df_states = (
    pd.read_excel("./datasets/NFHS345.xlsx", sheet_name=1, dtype=str)
    # drop blanks for Indicator Type (new file)
    .dropna(subset=["Indicator Type"])
    # standardize Indicator Types (new file)
    .replace(
        {
            "Indicator Type": {
                "Tobacco Use and Alcohol Consumption among Adults (age 15-49 years)": "Tobacco Use and Alcohol Consumption among Adults (age 15 years and above)"
            }
        }
    )
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

# miss information treatment for gender (new file exceptions)
df_states.loc[
    df_states.Indicator == "All women age 15-19 years who are anaemic (%)", "Gender"
] = np.nan
df_states.loc[
    df_states.Indicator == "Women who use any kind of tobacco (%)", "Gender"
] = np.nan
df_states.loc[
    df_states.Indicator == "Men age 15 years and above who use any kind of tobacco (%)",
    "Gender",
] = np.nan
df_states.loc[
    df_states.Indicator == "Women age 15 years and above who consume alcohol (%)",
    "Gender",
] = np.nan
df_states.loc[
    df_states.Indicator == "Men age 15 years and above who consume alcohol (%)",
    "Gender",
] = np.nan
df_states.loc[
    df_states.Indicator == "Ever undergone a breast examination for breast cancer (%)",
    "Gender",
] = np.nan
df_states.loc[
    df_states.Indicator == "Ever undergone a screening test for cervical cancer (%)",
    "Gender",
] = np.nan
df_states.loc[
    (
        (
            df_states.Indicator
            == "Ever undergone an oral cavity examination for oral cancer (%)"
        )
        & (
            df_states["Indicator Type"]
            == "Women Age 15-49 Years Who Have Ever Undergone Examinations of:"
        )
    ),
    "Gender",
] = "Female"
# miss information treatment for Indicator Type (new file exceptions)
df_states.loc[
    df_states.Indicator == "Births attended by skilled health personnel (%)",
    "Indicator Type",
] = "Delivery Care (for births in the 5 years before the survey)"
df_states.loc[
    df_states.Indicator == "Ever undergone a breast examination for breast cancer (%)",
    "Indicator Type",
] = "Women Age 15-49 Years Who Have Ever Undergone Examinations of:"
df_states.loc[
    df_states.Indicator == "Ever undergone a screening test for cervical cancer (%)",
    "Indicator Type",
] = "Women Age 15-49 Years Who Have Ever Undergone Examinations of:"
df_states.loc[
    (
        (
            df_states.Indicator
            == "Ever undergone an oral cavity examination for oral cancer (%)"
        )
        & (
            df_states["Indicator Type"]
            == "Women Age 15-49 Years Who Have Ever Undergone Examinations of:"
        )
    ),
    "Indicator Type",
] = "Screening for Cancer among Adults (age 30-49 years)"
df_states.loc[
    df_states.Indicator == "Institutional births (%)",
    "Indicator Type",
] = "Delivery Care (for births in the 5 years before the survey)"
df_states.loc[
    df_states.Indicator == "Men who are overweight or obese (BMI =25.0 kg/m) (%)",
    "Indicator Type",
] = "Nutritional Status of Adults (age 15-49 years)"
df_states.loc[
    df_states.Indicator
    == "Men whose Body Mass Index (BMI) is below normal (BMI <18.5 kg/m) (%)",
    "Indicator Type",
] = "Nutritional Status of Adults (age 15-49 years)"
df_states.loc[
    df_states.Indicator
    == "Mothers who consumed iron folic acid for 100 days or more when they were pregnant (%)",
    "Indicator Type",
] = "Maternity Care (for last birth in the 5 years before the survey)"
df_states.loc[
    df_states.Indicator
    == "Mothers who received postnatal care from a doctor/nurse/LHV/ANM/midwife/other health personnel within 2 days of delivery (%)",
    "Indicator Type",
] = "Maternity Care (for last birth in the 5 years before the survey)"
df_states.loc[
    df_states.Indicator == "Total unmet need (%)",
    "Indicator Type",
] = "Current Use of Family Planning Methods (currently married women age 15–49 years)"
df_states.loc[
    df_states.Indicator == "Unmet need for spacing (%)",
    "Indicator Type",
] = "Current Use of Family Planning Methods (currently married women age 15–49 years)"
df_states.loc[
    df_states.Indicator == "Women who are overweight or obese (BMI =25.0 kg/m) (%)",
    "Indicator Type",
] = "Nutritional Status of Adults (age 15-49 years)"
df_states.loc[
    df_states.Indicator
    == "Women whose Body Mass Index (BMI) is below normal (BMI <18.5 kg/m) (%)",
    "Indicator Type",
] = "Nutritional Status of Adults (age 15-49 years)"

# print for Rakesh missing gender entries (ignore Indicator Type)
mask_state_dup = df_states[
    df_states.duplicated(
        subset=["Indicator", "State", "Gender", "NFHS"],
        keep=False,
    )
].sort_values(["State", "Indicator"])
print(f"RAKESH - missing gender in {len(mask_state_dup)} rows in states data:")
print(mask_state_dup.values)

# prepare file to print-out and deliver to Rakesh
list_msg_out.append("NFHS345.xlsx")
list_msg_out.append(
    f"RAKESH - missing gender in {len(mask_state_dup)} rows in states data:"
)
list_msg_out.append(", ".join(mask_state_dup.columns))
for idx, a_row in mask_state_dup.iterrows():
    list_msg_out.append(", ".join(a_row.values.astype(str)))

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
            # DO NOT ingest separated india file (suggested by Rakesh)
            # df_india_45,
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
# enhance Indicator name with Gender to avoid duplicated Indicator names
df_nfhs_345.loc[df_nfhs_345.Gender.notna(), "Indicator"] = df_nfhs_345[
    df_nfhs_345.Gender.notna()
][["Indicator", "Gender"]].agg(" - ".join, axis=1)

# retain Indicator Types - Indicator combinations
nfhs_345_ind_df = df_nfhs_345.groupby(
    ["Indicator Type", "Indicator"], sort=False, as_index=False
).size()

# indicator indexed combinations for dash tree
nfhs_345_ind_types = sorted(nfhs_345_ind_df["Indicator Type"].unique(), key=str.lower)
states_kpi_index = {}
for i, ind_type in enumerate(nfhs_345_ind_types):
    ind_in_type = sorted(
        nfhs_345_ind_df.query("`Indicator Type` == @ind_type").Indicator.values,
        key=str.lower,
    )
    states_kpi_index.update(
        {f"{i}-{j}": indicator for j, indicator in enumerate(ind_in_type)}
    )

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
# detect uncleaned data in numerical columns
num_cols = ["Urban", "Rural", "Total"]
# prepare file to print-out and deliver to Rakesh
mask_nan_arrays = np.logical_or.reduce(
    [
        pd.to_numeric(df_nfhs_345[col], errors="coerce").isnull()
        & ~df_nfhs_345[col].isnull()
        for col in num_cols
    ]
)
mask_a_null_arrays = np.logical_or.reduce(
    [df_nfhs_345[col].isnull() for col in num_cols]
)

list_msg_out.append(
    f"RAKESH - PRESENCE of NON-NUMERICS in {mask_nan_arrays.sum()} rows in states data:"
)
for idx, a_row in df_nfhs_345[mask_nan_arrays].iterrows():
    list_msg_out.append(", ".join(a_row.values.astype(str)))

list_msg_out.append(
    f"RAKESH - PRESENCE of NULLS in {(mask_a_null_arrays & ~mask_nan_arrays).sum()} rows in states data:"
)
for idx, a_row in df_nfhs_345[mask_a_null_arrays & ~mask_nan_arrays].iterrows():
    list_msg_out.append(", ".join(a_row.values.astype(str)))


# filter uncleaned data in numerical columns
for col in num_cols:
    filter_na_345 = df_nfhs_345[col].isnull()
    filter_non_num_345 = pd.to_numeric(df_nfhs_345[col], errors="coerce").isnull()
    # non numerics
    print("Ask RAKESH about PRESENCE of NON-NUMERICS")
    print(df_nfhs_345[filter_non_num_345 & ~filter_na_345][col].values)
    # transform non-num to NaN
    df_nfhs_345.loc[:, col] = (
        df_nfhs_345[col].apply(pd.to_numeric, errors="coerce").astype("float64")
    )

    # negatives detected
    filter_neg_345 = df_nfhs_345[col] < 0
    print("Ask RAKESH about PRESENCE of NEGATIVES")
    print(
        f"No negatives for df column {col}"
        if df_nfhs_345[filter_neg_345].empty
        else df_nfhs_345[filter_neg_345].values
    )
    # take negatives in absolute value
    df_nfhs_345.loc[df_nfhs_345[col] < 0, col] = df_nfhs_345[df_nfhs_345[col] < 0][
        col
    ].abs()


# %%
# state names district/state data missmatches
district_state_match = {
    "Andaman & Nicobar": "Andaman & Nicobar Islands",
    "DNH": "Dadra & Nagar Haveli",
    "Maharastra": "Maharashtra",
    "NCT of Delhi": "Delhi",
    "All India Aspirational": "All India",
    "All India Gavi": "All India",
    "All India LaQshya": "All India",
}

# %%
# read table for indicators organization
equity_org_df = pd.read_excel(
    "./datasets/Equity_Analysis.xlsx", sheet_name="Template", dtype=str
)
# indicators sheet name column
ind_data_col = "Indicator_sheet"

# single ingestion pd.series
single_ing = (
    equity_org_df[ind_data_col]
    .dropna()
    .value_counts()
    .reset_index()
    .query("Indicator_sheet == 1")["index"]
)
# multi ingestion array
multi_ing = np.setdiff1d(equity_org_df.Indicator_sheet.dropna(), single_ing)

# equity data column (categories)
equity_data_col = "Equity_Categories"
# equity domain column
equity_dom_col = "Equity_Domains"
# equity default category A
equity_cat_a_col = "Default_Cat_A"
# equity default category B
equity_cat_b_col = "Default_Cat_B"

# available disaggregation categories (must be unique)
all_disagg = equity_org_df[equity_data_col].dropna().unique()

# %%
# first design: do not share data between pages
# (assess performance later)
equity_df = pd.read_excel(
    "./datasets/Equity_Analysis.xlsx", sheet_name=None, dtype=str, header=2
)
# strip keys for robust performance in Excel Equity sheet names
equity_df = {key.strip(): value for key, value in equity_df.items()}

# pre-stablished states names in equity file
state_names_equity = [
    "Andaman and Nicobar Islands",
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chandigarh",
    "Chhattisgarh",
    "Dadra and Nagar Haveli",
    "Daman and Diu",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jammu and Kashmir",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Ladakh",
    "Lakshadweep",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Nct of Delhi",
    "Odisha",
    "Puducherry",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Telangana",
    "All India",
]

# %%
# equity xls: concat excel sheets per added indicator (single ingestion)
df_list_equity = []
for name in single_ing:
    equity_df[name]["Indicator"] = equity_org_df.query(
        "Indicator_sheet == @name"
    ).Indicator_name.item()
    df_list_equity.append(
        equity_df[name]
        .rename(
            columns={
                "Unnamed: 0": "State",
                "Unnamed: 1": "Total",
                "Unnamed: 14": "ST",
            }
        )
        .dropna(subset=["State", "Year"])
        # data cleaning in Excel files ("intermediate columns")
        .dropna(axis="columns", how="all")
    )

for ind_type in multi_ing:
    ind_type_df = equity_df[ind_type].rename(columns={"Unnamed: 0": "State"})
    ind_type_disagg = ind_type_df.columns[
        ~ind_type_df.columns.str.contains("unnamed|year|state", regex=True, case=False)
    ]
    ind_names_in_type = (
        ind_type_df.iloc[0, :]
        .reset_index()
        .rename(columns={"index": "col_name", 0: "ind_name"})
    )
    # year column particular treatment
    ind_type_df.rename(
        columns={ind_names_in_type.query("ind_name == 'Year'").col_name.item(): "Year"},
        inplace=True,
    )
    for name in equity_org_df.query("Indicator_sheet == @ind_type").Indicator_name:
        # extract columns by indicator name
        col_ext = ind_names_in_type.query("ind_name == @name").col_name.values
        ind_df = (
            ind_type_df[["State", *col_ext, "Year"]].dropna(subset=["State", "Year"])
            # data cleaning in Excel files ("intermediate columns")
            .dropna(axis="columns", how="all")
            # rename col_ext to match available disaggregation
            .rename(columns={k: v for k, v in zip(col_ext, ind_type_disagg)})
        )
        # add the indicator name
        ind_df["Indicator"] = name
        df_list_equity.append(ind_df)

df_equity = (
    pd.concat(df_list_equity, ignore_index=True)[
        ["State", *all_disagg, "Year", "Indicator"]
    ]
    .replace(
        {
            "Year": {
                "2015-16": "NFHS-4 (2015-16)",
                "2019-21": "NFHS-5 (2019-21)",
                "2019-2021": "NFHS-5 (2019-21)",
            }
        }
    )
    # standardize names in equity
    .replace(
        {"State": {rf"(?i)({v})": v for v in state_names_equity}},
        regex=True,
    )
    .replace(
        {
            "State": {
                r"(?i)(India)": "All India",
                r"(?i)(Jammu And Kashmir)": "Jammu and Kashmir",
                r"(?i)(Jammu & Kashmir)": "Jammu and Kashmir",
                r"(?i)(\bAndaman and Nicobar Island\b)": "Andaman and Nicobar Islands",
                r"(?i)(\bAndaman And Nicobar Islands\b)": "Andaman and Nicobar Islands",
                r"(?i)(\bAndaman & Nicobar Isl\b)": "Andaman and Nicobar Islands",
                r"(?i)(\bandaman and nicobar i\b)": "Andaman and Nicobar Islands",
                r"(?i)(\bDadra & Nagar Haveli\b)": "Dadra and Nagar Haveli",
                r"(?i)(\bdadra and nagar havel\b)": "Dadra and Nagar Haveli",
                r"(?:^|,)(Delhi)(?:,|$)": "Nct of Delhi",
                r"(?:^|,)(delhi)(?:,|$)": "Nct of Delhi",
                r"(?i)(Nct Of Delhi)": "Nct of Delhi",
            },
        },
        regex=True,
    )
    # astype linked with template ingestion variable all_disagg
    .astype({a_col: "float64" for a_col in all_disagg})
)

# data cleaning report for equity: print-out and deliver to Rakesh
num_cols_equity = df_equity.columns[1:-2]
mask_nan_in_equity = np.logical_or.reduce(
    [
        pd.to_numeric(df_equity[col], errors="coerce").isnull()
        & ~df_equity[col].isnull()
        for col in num_cols_equity
    ]
)
mask_a_null_equity = np.logical_or.reduce(
    [df_equity[col].isnull() for col in num_cols_equity]
)
mask_a_neg_equity = np.logical_or.reduce(
    [df_equity[col] < 0 for col in num_cols_equity]
)

# report equity data cleaning (sept. 2022 non-numeric free)
# Note dismissed error handling: num_cols_equity astype "float64"
list_msg_out.append("Equity_Analysis.xlsx")
list_msg_out.append(
    f"RAKESH - PRESENCE of NON-NUMERICS in {mask_nan_in_equity.sum()} rows in equity data:"
)
list_msg_out.append(", ".join(df_equity.columns))
for idx, a_row in df_equity[mask_nan_in_equity].iterrows():
    list_msg_out.append(", ".join(a_row.values.astype(str)))

list_msg_out.append(
    f"RAKESH - PRESENCE of NEGATIVES in {(mask_a_neg_equity & ~mask_nan_in_equity).sum()} rows in equity data:"
)
for idx, a_row in df_equity[mask_a_neg_equity & ~mask_nan_in_equity].iterrows():
    list_msg_out.append(", ".join(a_row.values.astype(str)))

list_msg_out.append(
    f"RAKESH - PRESENCE of NULLS in {(mask_a_null_equity & ~mask_nan_in_equity).sum()} rows in equity data:"
)
for idx, a_row in df_equity[mask_a_null_equity & ~mask_nan_in_equity].iterrows():
    list_msg_out.append(", ".join(a_row.values.astype(str)))

# equity kpis type and colour: report shown by Luigi (14/09/2022)
# equity min-max colour: [#ff9437ff, #ae4131ff]
equity_colours = [
    "#3e7cabff",
    "#64a0c9ff",
    "#0c5e3eff",
    "#348951ff",
    "#58a360ff",
    "#eb8d79ff",
    "#b7809fff",
    "#edc948ff",
    "#f5715dff",
    "#a8a8a8ff",
    "#b5ede6ff",
]

equity_kpi_types = {
    a_type: {
        "kpis": {
            f"{i}-{j}": a_name
            for j, a_name in enumerate(
                equity_org_df.query("Indicator_Type == @a_type").Indicator_name.values
            )
        },
        "colour": equity_colours[i] if i < len(equity_colours) else equity_colours[-1],
        "default": equity_org_df.query("Indicator_Type == @a_type")
        .Default_display.map({"True": True, "False": False})
        .values,
    }
    for i, a_type in enumerate(equity_org_df.Indicator_Type.dropna().unique())
}
# concat all "kpis" index into one dictionary
equity_kpi_index = {
    k: v
    for a_type_dict in equity_kpi_types.values()
    for k, v in a_type_dict["kpis"].items()
}

# join equity kpis type into data table
equity_kpi_type_df = pd.DataFrame(
    {
        "Indicator_Type": sum(
            [
                [a_type] * len(equity_kpi_types[a_type]["kpis"])
                for a_type in equity_kpi_types
            ],
            [],
        ),
        "Indicator": [
            a_kpi
            for a_type in equity_kpi_types
            for a_kpi in equity_kpi_types[a_type]["kpis"].values()
        ],
        "Type_colour": sum(
            [
                [equity_kpi_types[a_type]["colour"]]
                * len(equity_kpi_types[a_type]["kpis"])
                for a_type in equity_kpi_types
            ],
            [],
        ),
    }
)

# %%
# domains and categories: equity page dynamic design
equity_dom_cat = {
    a_dom: {
        "categories": equity_org_df.query(f"`{equity_dom_col}` == '''{a_dom}'''")[
            equity_data_col
        ].values,
        "a_b_categories": np.concatenate(
            [
                equity_org_df.query(
                    f"`{equity_dom_col}` == '''{a_dom}''' & `{equity_cat_a_col}` == 'True'"
                )[equity_data_col].values,
                equity_org_df.query(
                    f"`{equity_dom_col}` == '''{a_dom}''' & `{equity_cat_b_col}` == 'True'"
                )[equity_data_col].values,
            ]
        ),
    }
    for a_dom in equity_org_df[equity_dom_col].dropna().unique()
}

# %%
# aspirational and other districts classification
aspir_dist_df = pd.read_excel(
    "./datasets/Aspirational Districts in India.xlsx",
    sheet_name=0,
    dtype=str,
    skiprows=1,
).replace(
    {
        "State ": {
            "Jammu And Kashmir": "Jammu & Kashmir",
            "Maharashtra": "Maharastra",
            "Uttar Pradesh ": "Uttar Pradesh",
        }
    }
)
# drop row duplicated
aspir_dist_df = aspir_dist_df[
    ~aspir_dist_df.Districts.str.contains("Dakshin Bastar Dantewada")
].reset_index(drop=True)

# is aspirational or UNICEF supported
aspir_dist_df["All India Aspirational"] = (
    aspir_dist_df.iloc[:, 3].notnull() | aspir_dist_df.iloc[:, 4].notnull()
)
aspir_dist_df["All India Gavi"] = aspir_dist_df.iloc[:, 5].notnull()
aspir_dist_df["All India LaQshya"] = aspir_dist_df.iloc[:, 6].notnull()

aspir_dist_df["State, District"] = aspir_dist_df[["State ", "Districts"]].agg(
    ",".join, axis=1
)

# %%
asp_dist_match = {
    "Andhra Pradesh,Kadapa": "Andhra Pradesh,Y.S.R.",
    "Andhra Pradesh,Vishakhapatnam": "Andhra Pradesh,Visakhapatnam",
    "Bihar,Champaran East": "Bihar,Purba Champaran",
    "Bihar,Champaran West": "Bihar,Pashchim Champaran",
    "Chhattisgarh,Kondagaon": "Chhattisgarh,Kodagaon",
    "Gujarat,Dahod": "Gujarat,Dohad",
    "Jharkhand,Sahebganj": "Jharkhand,Sahibganj",
    "Jharkhand,West Singhbhum ": "Jharkhand,Pashchimi Singhbhum",
    "Kerala,Wayand": "Kerala,Wayanad",
    "Madhya Pradesh,Satana": "Madhya Pradesh,Satna",
    "Tamil Nadu,Ramanathpuram": "Tamil Nadu,Ramanathapuram",
    "Telangana,Asifabad (Adilabad)": "Telangana,Adilabad",
    "Telangana,Bhadradri-Kothagudem": "Telangana,Bhadradri Kothagudem",
    "Telangana,Bhoopalapalli (Warangal)": "Telangana,Warangal",
    "Telangana,Mahbubnagar": "Telangana,Mahabubnagar",
    "Uttar Pradesh,Amroha": "Uttar Pradesh,Jyotiba Phule Nagar",
    "Uttar Pradesh,Badaun": "Uttar Pradesh,Budaun",
    "Uttar Pradesh,Badohi": "Uttar Pradesh,Sant Ravidas Nagar (Bhadohi)",
    "Uttar Pradesh,Barabanki": "Uttar Pradesh,Bara Banki",
    "Uttar Pradesh,Bulandshahar": "Uttar Pradesh,Bulandshahr",
    "Uttar Pradesh,Ferozabad": "Uttar Pradesh,Firozabad",
    "Uttar Pradesh,Gautam Budh Nagar": "Uttar Pradesh,Gautam Buddha Nagar",
    "Uttar Pradesh,Hathras": "Uttar Pradesh,Mahamaya Nagar",
    "Uttar Pradesh,Kanpur(Dehat)": "Uttar Pradesh,Kanpur Dehat",
    "Uttar Pradesh,Kanpur(Nagar)": "Uttar Pradesh,Kanpur Nagar",
    "Uttar Pradesh,Kasganj": "Uttar Pradesh,Kanshiram Nagar",
    "Uttar Pradesh,Maharajganj": "Uttar Pradesh,Mahrajganj",
    "Uttar Pradesh,Raebareli": "Uttar Pradesh,Rae Bareli",
    "West Bengal,Malda": "West Bengal,Maldah",
}

aspir_dist_df.replace({"State, District": asp_dist_match}, inplace=True)

# data entry error by UNICEF ICO: previous replacement produces duplicates
print("Ask RAKESH about DUPLICATES in ASPIRATIONALS:")
print(aspir_dist_df[aspir_dist_df.duplicated(subset=["State, District"], keep=False)])

# drop duplicates in aspirationals: keep first record
aspir_dist_df = aspir_dist_df.drop_duplicates(
    subset=["State, District"],
    keep="first",
    ignore_index=True,
).set_index("State, District")

# manually checked to make data entry consistent with duplicates dropped
checked_aspir_entries = {
    "Bihar,Darbhanga": {"All India Aspirational": True},
    "Bihar,Supaul": {"All India Aspirational": True},
    "Jharkhand,Pashchimi Singhbhum": {"All India LaQshya": True},
    "Rajasthan,Barmer": {"All India Gavi": True},
    "Rajasthan,Jaisalmer": {"All India Gavi": True},
}

for an_entry in checked_aspir_entries:
    aspir_dist_df.loc[
        an_entry, checked_aspir_entries[an_entry].keys()
    ] = checked_aspir_entries[an_entry].values()


# %%
# write output file to DBFS
out_filename = "etl_print_out.txt"
with open(out_filename, "w") as local_file:
    local_file.write("\n".join(list_msg_out))


# %%
# # check dictionary validation
# count_aspi = 0
# for an_aspi in aspir_dist_df["State, District"].values:
#     count_aspi += (
#         data_st_dt_df["State, District"] == asp_dist_match.get(an_aspi, an_aspi)
#     ).sum()

# match aspirational districts with reported NFHS by Rakesh (Excel files)
# asp_dist_match = [
#     get_close_matches(
#         dist,
#         data_st_dt_df["State, District"],
#         n=1,
#         cutoff=0.6,
#     )
#     for dist in np.setdiff1d(
#         aspir_dist_df["State, District"], data_st_dt_df["State, District"]
#     )
# ]
