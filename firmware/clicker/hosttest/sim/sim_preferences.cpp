// Stand-in for Preferences (NVS): key=value lines in a file, so the simulated clicker
// keeps its secret across restarts, like the real flash does.
#include <cstdlib>
#include <fstream>
#include <map>
#include <string>

#include "Preferences.h"
#include "sim_state.h"

namespace
{

  std::map<std::string, std::string> loadPrefs(const std::string &path)
  {
    std::map<std::string, std::string> values;
    std::ifstream in(path.c_str());
    std::string line;
    while (std::getline(in, line))
    {
      const size_t eq = line.find('=');
      if (eq != std::string::npos)
        values[line.substr(0, eq)] = line.substr(eq + 1);
    }
    return values;
  }

  void savePrefs(const std::string &path, const std::map<std::string, std::string> &values)
  {
    std::ofstream out(path.c_str());
    for (std::map<std::string, std::string>::const_iterator it = values.begin();
         it != values.end(); ++it)
    {
      out << it->first << "=" << it->second << "\n";
    }
  }

} // namespace

bool Preferences::begin(const char *name, bool readOnly, const char *partition_label)
{
  (void)readOnly;
  (void)partition_label;
  const char *path = getenv("CLICKER_SIM_NVS");
  char fallback[96];
  snprintf(fallback, sizeof(fallback), "build/nvs-%012llx-%s.txt",
           static_cast<unsigned long long>(simMac()), name);
  path_ = path ? path : fallback;
  return true;
}

void Preferences::end() {}

bool Preferences::isKey(const char *key) { return loadPrefs(path_).count(key) > 0; }

String Preferences::getString(const char *key, String defaultValue)
{
  std::map<std::string, std::string> values = loadPrefs(path_);
  return values.count(key) ? String(values[key]) : defaultValue;
}

size_t Preferences::putString(const char *key, const char *value)
{
  std::map<std::string, std::string> values = loadPrefs(path_);
  values[key] = value;
  savePrefs(path_, values);
  return strlen(value);
}

bool Preferences::remove(const char *key)
{
  std::map<std::string, std::string> values = loadPrefs(path_);
  if (values.erase(key) == 0)
    return false;
  savePrefs(path_, values);
  return true;
}
