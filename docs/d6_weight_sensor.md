# Individual Sensor Testing

# HX711 Weight Sensor with MAX32630FTHR board

### Goal

Interfacing HX711 weight sensor with MAX32630fthr board.

### Final working setup

**Hardware:** MAX32630FTHR, NHX711 Weight sensor 5Kg

**Wiring** :
| Weight Sensor  | MAX32630FTHR |
|---|---|
| GND   | GND |
| VCC   | 3V3 |
| DT    | P5_5 (pin 45 in software) |
| DSCK  | P5_4 (pin 45 in software) |

  ![wifi serial monitor](../images/weight_sensor.PNG)— weight_sensor Connection.

**Code Snippet:**
 ![wifi serial monitor](../images/weight_sens.png)— weight_sensor Known mass value to change.

## Output:

  ![wifi serial monitor](../images/weight_output1.jpeg)— weight_sensor connection.

  ![wifi serial monitor](../images/weight_sensor_output.png)— weight_sensor calibration output with known weight.

 ![wifi firebase](../images/weight_output2.jpeg)— weight_sensor  output for objects with unknown weights.

  ![wifi serial monitor](../images/weight_output3.png)— weight_sensor  output for objects with unknown weights.


