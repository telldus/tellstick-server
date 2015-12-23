
Example: Zipato RFID
==========================================

Telldus does not support the RFID reader from Zipato.

http://www.zipato.com/default.aspx?id=24&pid=88&page=1&grupe=0,2_15,3_37,0

It can be used any way with some Lua code.

.. code::

  -- Change these
  local zipatoNodeId = 892

  local tags = {}
  -- Add tags below

  -- Example code from a tag
  -- tags[1] = {device=881, code={143, 188, 119, 84, 42, 0, 1, 4, 0, 0}};
  -- Code for entering 1-2-3-4 on the keyboard
  -- tags[2] = {device=813, code={49, 50, 51, 52, 0, 0, 0, 0, 0, 0}};

  -- Do not change below

  COMMAND_CLASS_USER_CODE = 0x63
  USER_CODE_SET = 0x01
  USER_CODE_REPORT = 0x03
  COMMAND_CLASS_ALARM = 0x71
  ALARM_REPORT = 0x05

  local zipatoNode = deviceManager:device(zipatoNodeId):zwaveNode()

  function compareTags(tag1, tag2)
  	for index, item in python.enumerate(tag2) do
  		if item ~= tag1[index+1] then
  			return false
  		end
  	end
  	return true
  end

  function configureTag(index)
  	local data = list.new(index, 1)
  	for key,code in pairs(tags[index]['code']) do
  		data.append(code)
  	end
  	zipatoNode:sendMsg(COMMAND_CLASS_USER_CODE, USER_CODE_SET, data)
  	print("A new tag was configured in the Zipato.")
  	print("This will be sent the next time the reader is awake")
  end

  function checkNewTag(code)
  	-- New tag received. Check if it should be configured?
  	for key,tag in pairs(tags) do
  		if compareTags(tag['code'], code) then
  			configureTag(key)
  			return
  		end
  	end
  	-- Not yet configured. Must be configured first.
  	print("New unknown tag received. Add this to the codes if this should be recognized")
  	print("Tag data is %s", code)
  end

  function handleAlarm(data)
  	if list.len(data) < 8 then
  		return
  	end

  	local event = data[5]
  	local tag = data[7]
  	local device = deviceManager:device(tags[tag]['device'])
  	if device == nil then
  		print("Device not found")
  	end
  	if event == 5 then
  		print("Away, tag %s", tag)
  		zipatoNode:sendMsg(0x20, 0x01, list.new(0xFF))
  		device:command("turnoff", nil, "RFID")
  	elseif event == 6 then
  		print("Home, tag %s", tag)
  		device:command("turnon", nil, "RFID")
  	end
  end

  function onZwaveMessageReceived(device, flags, cmdClass, cmd, data)
  	if device:id() ~= zipatoNodeId then
  		return
  	end
  	if cmdClass == COMMAND_CLASS_ALARM and cmd == ALARM_REPORT then
  		handleAlarm(data)
  		return
  	end
  	if cmdClass ~= COMMAND_CLASS_USER_CODE or cmd ~= USER_CODE_REPORT then
  		return
  	end
  	local identifier = data[0]
  	local status = data[1]
  	if identifier == 0 and status == 0 then
  		checkNewTag(list.slice(data,2))
  		return
  	end
  end

  -- This command clears all configured codes in the reader
  -- zipatoNode:sendMsg(COMMAND_CLASS_USER_CODE, USER_CODE_SET, list.new(0, 0))
