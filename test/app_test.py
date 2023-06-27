import os
import json


from corva import StreamTimeEvent, StreamTimeRecord
from lambda_function import lambda_handler
from constants import DATASET_PROVIDER, DATASET_NAME

TEST_STREAMS_PATH =  os.path.join(os.path.abspath(os.path.dirname(__file__)), 'streams')


class TestStreamCalculations():
    def test_dataset(self, app_runner, requests_mock):
        stream_file = os.path.join(TEST_STREAMS_PATH, "corva_wits.json")
        with open(stream_file, encoding="utf8") as raw_stream:
            wits_stream = json.load(raw_stream)
        stream_record_data = wits_stream[0]["data"]
        event = StreamTimeEvent(
            company_id=1,
            asset_id=1234,
            records=[
                StreamTimeRecord(
                    data=stream_record_data, timestamp=1620905165
                )
            ],
        )
        
        requests_mock.post(f'https://data.localhost.ai/api/v1/data/{DATASET_PROVIDER}/{DATASET_NAME}/')
        client_output = app_runner(lambda_handler, event=event)
        assert client_output
        assert "data" in client_output[0]
        assert client_output[0]["data"]["total_pump_spm"] == stream_record_data["pump_spm_1"] + stream_record_data["pump_spm_2"]



