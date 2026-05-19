from scripts.build_dashboard import prepare_records


def test_prepare_records_calculates_drawdown_and_forward_return():
    raw = {
        "Date": ["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05", "2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11", "2024-01-12"],
        "Open": [100, 99, 98, 97, 96, 94, 95, 96, 97],
        "High": [101, 100, 99, 98, 97, 95, 96, 97, 98],
        "Low": [99, 98, 97, 96, 95, 93, 94, 95, 96],
        "Close": [100, 99, 98, 97, 96, 94, 95, 96, 97],
        "Volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800],
    }

    import pandas as pd

    records = prepare_records(pd.DataFrame(raw))
    event_row = records[5]

    assert event_row["date"] == "2024-01-09"
    assert round(event_row["drawdown_5d"], 4) == -0.06
    assert round(event_row["forward_return_3d"], 4) == round(97 / 94 - 1, 4)

