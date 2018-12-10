Mode
####

Description
***********
Modes are used to indicate what's going on (?) in a Room at the moment, so that for example Events can take this into account when triggered. A Mode could for example be "Empty", "Movie mode", "Romantic mode", or "Vacation mode", "Away", "Home" (we need to discuss the suggested names, how Modes should be looked at, more closely, suffixing with " mode" perhaps makes it more clear).


Convention
**********

* A Mode, and one Mode only, can be assigned to any Room (or Gateway?).
* A Mode can be used as a condition in Events (and Schedules?), in combination with a Room/Gateway.
* A Mode can be set manually or in an Event Action.
* Switching of Mode can activate a scene (?).
* If a Room has no mode, parent Room/Gateway Mode is used. If it has none, continue check parents until top level.
* When switching Mode on a Room, it's possible to choose if the Modes of sub rooms should be cleared or not, so that the new Mode is assigned to them too.

