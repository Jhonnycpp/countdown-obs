import obspython as obs
from enum import IntEnum, auto
from datetime import datetime, timedelta, tzinfo

class IncrementUnit(IntEnum):
  SECONDS = auto()
  MINUTES = auto()
  HOURS = auto()

class TimeFormat(IntEnum):
  SECONDS = auto()
  MINUTES = auto()
  HOURS = auto()

class Timer:
  def __init__(self, source: str = "", time_format: TimeFormat = TimeFormat.HOURS, increment: int = 10, increment_unit: IncrementUnit = IncrementUnit.MINUTES, duration: timedelta = 0):
      self.source = source
      self.time_format = time_format
      self.increment = increment
      self.increment_unit = increment_unit
      self.duration = duration
      self.start_at = 0
      self.__diff = 0
  
  def __repr__(self):
    return "<Timer source:%s time_format:%s increment:%s increment_unit:%s duration:%s>" % (self.source, self.time_format, self.increment, self.increment_unit, self.duration)

  def __format_time(self):
    sec = int(self.__diff)
    mins = sec// 60
    sec = sec % 60
    hours = mins // 60
    mins = mins % 60

    switcher = {
      TimeFormat.SECONDS: "{:02d}:{:02d}:{:02d}".format(hours, mins, sec),
      TimeFormat.MINUTES: "{:02d}:{:02d}".format(hours, mins),
      TimeFormat.HOURS: "{:02d}".format(hours),
    }
    return switcher.get(self.time_format, "{:02d}:{:02d}:{:02d}".format(hours, mins, sec))

  def reset(self):
    self.increment = 10
    self.increment_unit = IncrementUnit.MINUTES
    self.time_format = TimeFormat.SECONDS
    self.__diff = 0
  
  def stopwatch(self):
    now = datetime.now()
    source = obs.obs_get_source_by_name(self.source)
    self.__diff = ((self.start_at + self.duration) - now).total_seconds()
    if self.__diff == 0:
        obs.timer_remove(self.stopwatch)
        obs.remove_current_callback()
    elif self.__diff < 0:
        obs.timer_remove(self.stopwatch)
        obs.remove_current_callback()
        self.__diff = 0
    try:
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", str(self.__format_time()))
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
    except UnboundLocalError:
        pass

  def postpone(self):
    switcher = {
      IncrementUnit.SECONDS: timedelta(seconds=self.increment),
      IncrementUnit.MINUTES: timedelta(minutes=self.increment),
      IncrementUnit.HOURS: timedelta(hours=self.increment),
    }
    self.duration += switcher.get(self.increment_unit, timedelta(minutes=self.increment))

print("Reloaded")
currentTimer = Timer()

def run(props, prop):
  global currentTimer

  currentTimer.start_at = datetime.now()

  print(currentTimer)

  obs.timer_remove(currentTimer.stopwatch)
  obs.timer_add(currentTimer.stopwatch, 200)

def postpone(props, prop):
  global currentTimer

  currentTimer.postpone()

def scene_updater():
  global currentTimer
  obs.obs_source_release(obs.obs_get_source_by_name(currentTimer.source))

##############################################################################
#                                  OBS                                       #
##############################################################################

def script_update(settings):
  print("script_update")
  global currentTimer
  currentTimer.increment = obs.obs_data_get_int(settings, "increment")
  currentTimer.increment_unit = obs.obs_data_get_int(settings, "increment_unit")
  currentTimer.source = obs.obs_data_get_string(settings, "source")
  currentTimer.time_format = obs.obs_data_get_int(settings, "timer_format")
  
  duration = obs.obs_data_get_string(settings, "duration")
  try:
    date_time = datetime.strptime(duration, "%H:%M")
    currentTimer.duration = date_time - datetime(1900, 1, 1)
  except Exception as err:
    obs.script_log(obs.LOG_WARNING, "Error parsing initial time" + err.reason)
    obs.remove_current_callback()

  obs.timer_remove(scene_updater)
  if currentTimer.source != "":
    obs.timer_add(scene_updater, 1000)

def script_unload():
  obs.timer_remove(currentTimer.stopwatch)
  obs.timer_remove(scene_updater)

def script_defaults(settings):
  print("default")
  global currentTimer

  obs.obs_data_set_default_int(settings, "increment_unit", IncrementUnit.MINUTES)
  obs.obs_data_set_default_int(settings, "increment", 10)
  obs.obs_data_set_default_int(settings, "timer_format", TimeFormat.SECONDS)
  obs.obs_data_set_default_string(settings, "duration", "03:00")

  currentTimer.reset()

def script_description():
  return "aaaaaa"

def script_properties():
  props = obs.obs_properties_create()

  sources_text_combobox = obs.obs_properties_add_list(props, "source", "Text Source", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
  
  obs.obs_property_list_add_string(sources_text_combobox, "", "")

  sources = obs.obs_enum_sources()
  if sources is not None:
    for source in sources:
      name = obs.obs_source_get_name(source)
      source_id = obs.obs_source_get_unversioned_id(source)
      if source_id == "text_gdiplus" or source_id == "text_ft2_source":
          name = obs.obs_source_get_name(source)
          obs.obs_property_list_add_string(sources_text_combobox, name, name)
    obs.source_list_release(sources)

  obs.obs_properties_add_int_slider(props, "increment", "How much increment:", 1, 60, 1)
  increment_obs_combobox = obs.obs_properties_add_list(props, "increment_unit", "Increment unit:", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
  
  obs.obs_property_list_add_int(increment_obs_combobox, "Seconds", IncrementUnit.SECONDS)
  obs.obs_property_list_add_int(increment_obs_combobox, "Minutes", IncrementUnit.MINUTES)
  obs.obs_property_list_add_int(increment_obs_combobox, "Hours", IncrementUnit.HOURS)

  timer_format_obs_combobox = obs.obs_properties_add_list(props, "timer_format", "Timer format:", 
  obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_INT)
  
  obs.obs_property_list_add_int(timer_format_obs_combobox, "HH:MM:SS", TimeFormat.SECONDS)
  obs.obs_property_list_add_int(timer_format_obs_combobox, "HH:MM", TimeFormat.MINUTES)
  obs.obs_property_list_add_int(timer_format_obs_combobox, "HH", TimeFormat.HOURS)

  obs.obs_properties_add_text(props, "duration", "Duration (HH:MM):", obs.OBS_TEXT_DEFAULT)

  obs.obs_properties_add_button(props, "run", "Run/Restart Timer", run)

  obs.obs_properties_add_button(props, "btn_increment", "increment", postpone)

  return props
