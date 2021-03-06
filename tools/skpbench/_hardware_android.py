# Copyright 2016 Google Inc.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import print_function
from _hardware import Hardware
import sys
import time

class HardwareAndroid(Hardware):
  def __init__(self, adb):
    Hardware.__init__(self)
    self.warmup_time = 5
    self._adb = adb

    if self._adb.root():
      self._adb.remount()

  def __enter__(self):
    Hardware.__enter__(self)
    if not self._adb.is_root() and self._adb.root():
      self._adb.remount()

    self._adb.shell('\n'.join([
      # turn on airplane mode.
      '''
      settings put global airplane_mode_on 1''',

      # disable GPS.
      '''
      settings put secure location_providers_allowed -gps
      settings put secure location_providers_allowed -wifi
      settings put secure location_providers_allowed -network''']))

    if self._adb.is_root():
      self._adb.shell('\n'.join([
        # disable bluetooth, wifi, and mobile data.
        '''
        service call bluetooth_manager 8
        svc wifi disable
        svc data disable''',

        # kill the gui.
        '''
        setprop ctl.stop media
        setprop ctl.stop zygote
        setprop ctl.stop surfaceflinger
        setprop ctl.stop drm''',

        # disable ASLR
        '''
        echo 0 > /proc/sys/kernel/randomize_va_space''']))
    else:
      print("WARNING: no adb root access; results may be unreliable.",
            file=sys.stderr)

    return self

  def __exit__(self, exception_type, exception_value, traceback):
    Hardware.__exit__(self, exception_type, exception_value, traceback)
    self._adb.reboot() # some devices struggle waking up; just hard reboot.

  def sanity_check(self):
    Hardware.sanity_check(self)

  def print_debug_diagnostics(self):
    # search for and print thermal trip points that may have been exceeded.
    self._adb.shell('''\
      THERMALDIR=/sys/class/thermal
      if [ ! -d $THERMALDIR ]; then
        exit
      fi
      for ZONE in $(cd $THERMALDIR; echo thermal_zone*); do
        cd $THERMALDIR/$ZONE
        if [ ! -e mode ] || grep -Fxqv enabled mode || [ ! -e trip_point_0_temp ]; then
          continue
        fi
        TEMP=$(cat temp)
        TRIPPOINT=trip_point_0_temp
        if [ $TEMP -le $(cat $TRIPPOINT) ]; then
          echo "$ZONE ($(cat type)): temp=$TEMP <= $TRIPPOINT=$(cat $TRIPPOINT)" 1>&2
        else
          let i=1
          while [ -e trip_point_${i}_temp ] &&
                [ $TEMP -gt $(cat trip_point_${i}_temp) ]; do
            TRIPPOINT=trip_point_${i}_temp
            let i=i+1
          done
          echo "$ZONE ($(cat type)): temp=$TEMP > $TRIPPOINT=$(cat $TRIPPOINT)" 1>&2
        fi
      done''')

    Hardware.print_debug_diagnostics(self)
