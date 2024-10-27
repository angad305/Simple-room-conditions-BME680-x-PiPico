import math

class IAQTracker:
    def __init__(self, burn_in_cycles=300, gas_recal_period=3600, ph_slope=0.03):
        self.slope = ph_slope
        self.burn_in_cycles = burn_in_cycles
        self.gas_cal_data = []
        self.gas_ceil = 0
        self.gas_recal_period = gas_recal_period
        self.gas_recal_step = 0

    def waterSatDensity(self, temp):
        rho_max = (6.112 * 100 * math.exp((17.62 * temp) / (243.12 + temp))) / (461.52 * (temp + 273.15))
        return rho_max

    def getIAQ(self, bme_data):
        temp = bme_data.temperature
        hum = bme_data.humidity
        R_gas = bme_data.gas_resistance

        rho_max = self.waterSatDensity(temp)
        hum_abs = hum * 10 * rho_max

        comp_gas = R_gas * math.exp(self.slope * hum_abs)

        if self.burn_in_cycles > 0:
            self.burn_in_cycles -= 1
            if comp_gas > self.gas_ceil:
                self.gas_cal_data = [comp_gas]
                self.gas_ceil = comp_gas
            return None
        else:
            if comp_gas > self.gas_ceil:
                self.gas_cal_data.append(comp_gas)
                if len(self.gas_cal_data) > 100:
                    del self.gas_cal_data[0]
                self.gas_ceil = sum(self.gas_cal_data) / len(self.gas_cal_data)

            AQ = min((comp_gas / self.gas_ceil) ** 2, 1) * 100

            self.gas_recal_step += 1
            if self.gas_recal_step >= self.gas_recal_period:
                self.gas_recal_step = 0
                self.gas_cal_data.append(comp_gas)
                del self.gas_cal_data[0]
                self.gas_ceil = sum(self.gas_cal_data) / len(self.gas_cal_data)

        return AQ