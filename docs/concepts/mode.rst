Mode
####

Description
***********
Modes are used to indicate what's going on (?) in a Room at the moment, so that for example Events can take this into account when triggered. A Mode could for example be "Empty", "Movie mode", "Romantic mode", or "Vacation mode", "Away", "Home" (we need to discuss the suggested names, how Modes should be looked at, more closely, suffixing with " mode" perhaps makes it more clear).


Convention
**********

* A Mode, and one Mode only, can be assigned to any Room.
* A Mode can be used as a condition in Events, in combination with a Room/Gateway.
* A Mode can be set manually, in a Scene or in an Event Action.
* If a Room has no mode, parent Room/Gateway Mode is used. If it has none, continue check parents until top level.
* When switching Mode on a Room, it's possible to choose if the Modes of sub rooms should be cleared or not, so that the new Mode is assigned to them too.
* When switching Mode, it may trigger an Event.
