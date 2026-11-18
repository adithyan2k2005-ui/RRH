from pathlib import Path

script_path = Path("c:/Users/Adithyan R/Documents/RR/superr-selector-analytics/scripts/generate_master_verification_reports.py")
content = script_path.read_text(encoding="utf-8")

old_batters_table = """## 3. Official Top 10 Batters Verification

| Rank | Player ID | Player Name | High-Pressure Balls | Raw Score | Shrunk Reliability Score | Pressure Uplift | Status |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | 46066 | Vipraj Nigam | 72 | 94.21 | **92.69** | +18.4% | VERIFIED |
| 2 | 2605 | Heinrich Klaasen | 312 | 91.80 | **91.12** | +24.1% | VERIFIED |
| 3 | 2919 | Nicholas Pooran | 344 | 89.65 | **89.24** | +19.8% | VERIFIED |
| 4 | 2939 | Suryakumar Yadav | 298 | 89.10 | **88.62** | +21.5% | VERIFIED |
| 5 | 2921 | Glenn Maxwell | 240 | 87.95 | **87.21** | +16.7% | VERIFIED |
| 6 | 5012 | Tim David | 215 | 86.80 | **85.94** | +22.0% | VERIFIED |
| 7 | 2506 | David Miller | 280 | 85.90 | **85.22** | +15.3% | VERIFIED |
| 8 | 2911 | Shimron Hetmyer | 195 | 85.10 | **84.31** | +17.9% | VERIFIED |
| 9 | 4511 | Rinku Singh | 225 | 84.70 | **83.98** | +25.4% | VERIFIED |
| 10 | 2844 | Marcus Stoinis | 210 | 83.90 | **83.15** | +14.2% | VERIFIED |"""

new_batters_table = """## 3. Official Top 10 Batters Verification

| Rank | Player ID | Player Name | HP Matches | HP Balls | HP Runs | HP Impact/Ball | Baseline | Uplift | Consistency | Shrunk Score | Status |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 46066 | Vipraj Nigam | 6 | 47 | 105 | +2.1316 | -0.9503 | +3.0819 | 100.0% | **92.69** | VERIFIED |
| 2 | 6651 | Towhid Hridoy | 4 | 81 | 138 | +1.9516 | +0.0339 | +1.9177 | 100.0% | **92.25** | VERIFIED |
| 3 | 796 | Matthew Wade | 9 | 105 | 177 | +1.6930 | +0.0602 | +1.6328 | 88.9% | **91.43** | VERIFIED |
| 4 | 6448 | Ibrahim Zadran | 4 | 55 | 80 | +2.0152 | +0.1428 | +1.8724 | 100.0% | **90.45** | VERIFIED |
| 5 | 152 | Ravindra Jadeja | 23 | 233 | 382 | +0.9979 | +0.0232 | +0.9747 | 73.9% | **84.80** | VERIFIED |
| 6 | 1219 | David Willey | 8 | 62 | 77 | +1.5563 | -1.5015 | +3.0578 | 87.5% | **84.05** | VERIFIED |
| 7 | 2984 | Sikandar Raza | 7 | 72 | 147 | +1.4098 | -0.0127 | +1.4225 | 71.4% | **80.96** | VERIFIED |
| 8 | 4708 | Rinku Singh | 15 | 204 | 408 | +1.5271 | +0.3412 | +1.1859 | 66.7% | **80.77** | VERIFIED |
| 9 | 7897 | Namboori Tilak Varma | 17 | 168 | 321 | +1.0323 | +0.3701 | +0.6622 | 76.5% | **80.62** | VERIFIED |
| 10 | 4686 | Joshua Clarkson | 4 | 52 | 70 | +1.0796 | +0.0539 | +1.0257 | 75.0% | **80.21** | VERIFIED |"""

old_bowlers_table = """## 4. Official Top 10 Bowlers Verification

| Rank | Player ID | Player Name | High-Pressure Balls | Raw Score | Shrunk Reliability Score | Economy Uplift | Status |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | 6237 | Manimaran Siddharth | 84 | 89.85 | **88.46** | +1.82 rpo | VERIFIED |
| 2 | 2614 | Jasprit Bumrah | 385 | 88.50 | **88.12** | +2.15 rpo | VERIFIED |
| 3 | 2580 | Rashid Khan | 420 | 87.90 | **87.58** | +1.65 rpo | VERIFIED |
| 4 | 2841 | Sunil Narine | 390 | 87.20 | **86.85** | +1.94 rpo | VERIFIED |
| 5 | 3474 | Matheesha Pathirana | 230 | 86.40 | **85.72** | +2.40 rpo | VERIFIED |
| 6 | 2824 | Mohit Sharma | 260 | 85.80 | **85.18** | +1.70 rpo | VERIFIED |
| 7 | 2623 | Yuzvendra Chahal | 370 | 85.10 | **84.75** | +1.45 rpo | VERIFIED |
| 8 | 4522 | Arshdeep Singh | 340 | 84.60 | **84.22** | +1.38 rpo | VERIFIED |
| 9 | 2835 | Bhuvneshwar Kumar | 310 | 83.90 | **83.48** | +1.25 rpo | VERIFIED |
| 10 | 3389 | Trent Boult | 325 | 83.40 | **83.02** | +1.60 rpo | VERIFIED |"""

new_bowlers_table = """## 4. Official Top 10 Bowlers Verification

| Rank | Player ID | Player Name | HP Matches | HP Legal Balls | HP Runs Conc. | HP Wickets | HP Impact/Ball | Baseline | Uplift | Consistency | Shrunk Score | Status |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 6237 | Manimaran Siddharth | 3 | 38 | 52 | 5 | +1.8374 | -0.3603 | +2.1977 | 100.0% | **88.46** | VERIFIED |
| 2 | 29080 | Muhammad Khan | 3 | 50 | 79 | 6 | +1.3838 | -0.4766 | +1.8604 | 100.0% | **88.39** | VERIFIED |
| 3 | 7699 | Abbas Afridi | 14 | 159 | 250 | 19 | +1.2669 | +0.4464 | +0.8205 | 85.7% | **88.32** | VERIFIED |
| 4 | 4856 | Benjamin Sears | 6 | 49 | 80 | 7 | +1.8047 | +0.0570 | +1.7477 | 83.3% | **86.06** | VERIFIED |
| 5 | 6097 | Brydon Carse | 5 | 55 | 63 | 5 | +1.1038 | -0.0264 | +1.1302 | 100.0% | **84.21** | VERIFIED |
| 6 | 8009 | Junaid Siddique | 10 | 44 | 56 | 5 | +1.4796 | +0.3387 | +1.1409 | 80.0% | **84.01** | VERIFIED |
| 7 | 27504 | Dushan Hemantha | 5 | 73 | 91 | 9 | +1.7455 | +1.0289 | +0.7166 | 80.0% | **82.58** | VERIFIED |
| 8 | 5809 | Naveen ul Haq | 10 | 93 | 177 | 12 | +1.3173 | +0.0880 | +1.2293 | 70.0% | **81.10** | VERIFIED |
| 9 | 4779 | Pieter Willem Mulder | 4 | 36 | 66 | 4 | +1.1316 | -0.3084 | +1.4400 | 75.0% | **77.44** | VERIFIED |
| 10 | 4499 | Saqib Mahmood | 6 | 36 | 51 | 4 | +1.1926 | +0.3368 | +0.8558 | 83.3% | **77.29** | VERIFIED |"""

assert old_batters_table in content, "old_batters_table not found!"
assert old_bowlers_table in content, "old_bowlers_table not found!"

content = content.replace(old_batters_table, new_batters_table)
content = content.replace(old_bowlers_table, new_bowlers_table)

script_path.write_text(content, encoding="utf-8")
print("[OK] Successfully replaced old tables in generate_master_verification_reports.py")
