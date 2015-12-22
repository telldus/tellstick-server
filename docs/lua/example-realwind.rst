
Example: Real wind
==========================================

A thermometer measures the actual temperature but it is not the same as the
perceived temperature. To get perceived temperature you must also take the wind
into account. If TellStick ZNet has an anemometer this can be used to calculate
the perceived temperature.

The script below calculates this and gives the anemometer a thermometer value.

Source of the algorithm:
http://www.smhi.se/kunskapsbanken/meteorologi/vindens-kyleffekt-1.259

.. code::

  -- EDIT THESE

  local windSensor = 287
  local tempSensor = 297

  -- DO NOT EDIT BELOW THIS LINE

  local tempValue = deviceManager:device(tempSensor).sensorValue(1, 0)
  local windValue = deviceManager:device(windSensor).sensorValue(64, 0)

  function calculate()
    if tempValue == nil or windValue == nil then
      return
    end
    local w = math.pow(windValue, 0.16)
    local v = 13.12 + 0.6215*tempValue - 13.956*w + 0.48669*tempValue*w
    v = math.floor(v * 10 + 0.5) / 10
    local windDevice = deviceManager:device(windSensor)
    windDevice:setSensorValue(1, v, 0)
  end

  function onSensorValueUpdated(device, valueType, value, scale)
    if device:id() == windSensor and valueType == 64 and scale == 0 then
      windValue = value
      calculate()
    elseif device:id() == tempSensor and valueType == 1 and scale == 0 then
      tempValue = value
      calculate()
    end
  end
