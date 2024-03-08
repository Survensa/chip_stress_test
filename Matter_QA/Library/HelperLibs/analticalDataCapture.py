from typing import Any


class AnalyticalDataCapture:

    def __init__(self, analytics_json, test_config):
        self.analytics_json = analytics_json
        self.test_config = test_config
        for analytic in self.test_config.general_configs.analytics_parameters:
            self.analytics_json["analytics"].update({analytic: {}})

    def capture_analytics_to_json(self, analytics_name: str,
                                  analytics_data: Any, iteration_number: str):
        self.analytics_json["analytics"][analytics_name].update(
            {iteration_number: analytics_data})
