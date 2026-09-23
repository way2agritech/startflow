# AgMachineX

AgMachineX is a simple, farmer-friendly Streamlit prototype that helps a
farmer identify which categories of farm machinery are relevant to the
work they're planning, based on their work area, crops, land size, and
the specific tasks they need done.

This version deliberately does **not** rank, score, or recommend a
"best" machine — it only identifies the relevant machinery categories.

## 1. What the project does

The app walks the farmer through five simple steps:

```
Work Area → Crop Category → Land Size → Task → Machine Shortlist
```

1. **Work Area** – the farmer picks one or more broad areas of work
   (e.g. Irrigation & Water, Harvest & Processing).
2. **Crop Category** – the farmer picks the crop categories relevant
   to that work area.
3. **Land Size** – the farmer enters the land area for each selected
   crop category (a single input if only one category was chosen,
   one input per category if multiple were chosen).
4. **Task** – the farmer picks the specific tasks they need
   machinery for, filtered from the dataset by work area + crop
   category.
5. **Machine Shortlist** – the app shows the deduplicated list of
   machinery categories relevant to the selected tasks.

No suitability scoring, AI recommendations, logins, or financial
calculations are included in this version.

## 2. Project structure

```
agmachinex/
│
├── app.py                  # Streamlit app: pages, navigation, session state
├── requirements.txt
├── README.md
│
├── data/
│   ├── work area(Work Areas).csv
│   └── agmachinex(machinery shortlist).csv
│
├── utils/
│   ├── data_loader.py       # CSV loading, validation, cleaning
│   └── logic.py              # Filtering, deduplication, area calculations
│
└── assets/
    └── style.css              # Visual styling
```

## 3. How to install dependencies

From inside the `agmachinex` folder:

```bash
pip install -r requirements.txt
```

## 4. How to run it

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints in your terminal (usually
`http://localhost:8501`).

## 5. Where to put the CSV files

Both CSV files must live inside the `data/` folder, with these exact
filenames:

- `data/work area(Work Areas).csv`
- `data/agmachinex(machinery shortlist).csv`

They are already included in this project. If you need to replace them
with updated data, keep the same filenames and column names described
below.

## 6. CSV column requirements

**`work area(Work Areas).csv`**

| Column                          | Notes                                   |
|----------------------------------|------------------------------------------|
| `Farmer-Friendly Description`   | The work area label shown to the farmer |

**`agmachinex(machinery shortlist).csv`**

| Column                    | Notes                                              |
|----------------------------|-----------------------------------------------------|
| `Category of Crops`        | Crop category (shown on the Crop Category page)   |
| `Category of Operations`   | Must match a value from the Work Areas CSV        |
| `Operation / Task`         | The task shown on the Task page                    |
| `Machinery Category`       | The machine shown on the final shortlist          |
| `Attachment`               | Optional attachment info (not shown to the farmer in this version) |

The app reads these files fresh on first load (cached for
performance), strips extra whitespace, drops fully empty rows, and
will show a clear developer-facing error if a required file or
column is missing — it will not silently invent data.

## 7. Current application flow

```
START
  ↓
WORK AREA            (from Work Areas CSV, multi-select)
  ↓
CROP CATEGORY        (from machinery CSV, filtered by work area, multi-select)
  ↓
LAND SIZE            (one input per selected crop category)
  ↓
TASK                 (from machinery CSV, filtered by work area + crop category, multi-select)
  ↓
MACHINE SHORTLIST    (deduplicated machinery categories, with underlying
                       crop/task relationships retained internally)
```

Selections persist as the farmer moves back and forth between steps
via Streamlit's session state — nothing is lost when going back.
