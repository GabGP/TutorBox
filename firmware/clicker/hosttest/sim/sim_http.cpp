// Stand-in for HTTPClient: real HTTP/1.1, one request per connection, so the simulated
// clicker talks to an actual Utz'tutor backend.
#include <arpa/inet.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <cerrno>
#include <cstdlib>
#include <sstream>
#include <string>

#include "HTTPClient.h"
#include "sim_state.h"

bool HTTPClient::begin(WiFiClient &client, String url)
{
  (void)client;
  std::string text = url.c_str();
  const std::string scheme = "http://";
  if (text.compare(0, scheme.size(), scheme) != 0)
    return false;
  text = text.substr(scheme.size());
  const size_t slash = text.find('/');
  std::string hostPort = text.substr(0, slash);
  path_ = slash == std::string::npos ? "/" : text.substr(slash);
  const char *override = getenv("CLICKER_SIM_SERVER");
  if (override != nullptr)
    hostPort = override;
  const size_t colon = hostPort.find(':');
  host_ = hostPort.substr(0, colon);
  port_ = colon == std::string::npos ? 80 : atoi(hostPort.c_str() + colon + 1);
  headers_.clear();
  body_.clear();
  return true;
}

void HTTPClient::end(void) { headers_.clear(); }
void HTTPClient::setReuse(bool reuse) { reuse_ = reuse; }
void HTTPClient::setConnectTimeout(int32_t connectTimeout) { (void)connectTimeout; }
void HTTPClient::setTimeout(uint16_t timeout) { timeoutMs_ = timeout; }

void HTTPClient::addHeader(const String &name, const String &value, bool first,
                           bool replace)
{
  (void)first;
  (void)replace;
  headers_.push_back(std::string(name.c_str()) + ": " + value.c_str());
}

int HTTPClient::GET() { return perform("GET", nullptr, 0); }

int HTTPClient::POST(uint8_t *payload, size_t size)
{
  return perform("POST", payload, size);
}

int HTTPClient::perform(const char *method, const uint8_t *payload, size_t size)
{
  body_.clear();
  status_ = 0;
  bodyUntilClose_ = false;
  if (!simWifiUp())
    return HTTPC_ERROR_NOT_CONNECTED;
  addrinfo hints;
  memset(&hints, 0, sizeof(hints));
  hints.ai_family = AF_INET;
  hints.ai_socktype = SOCK_STREAM;
  addrinfo *found = nullptr;
  if (getaddrinfo(host_.c_str(), std::to_string(port_).c_str(), &hints, &found) != 0)
  {
    return HTTPC_ERROR_CONNECTION_REFUSED;
  }
  const int fd = socket(found->ai_family, found->ai_socktype, found->ai_protocol);
  timeval tv;
  tv.tv_sec = timeoutMs_ / 1000;
  tv.tv_usec = (timeoutMs_ % 1000) * 1000;
  setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
  setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));
  const int connected = connect(fd, found->ai_addr, found->ai_addrlen);
  freeaddrinfo(found);
  if (connected != 0)
  {
    close(fd);
    return HTTPC_ERROR_CONNECTION_REFUSED;
  }
  std::ostringstream request;
  request << method << " " << path_ << " HTTP/1.1\r\nHost: " << host_ << ":" << port_
          << "\r\n";
  for (size_t i = 0; i < headers_.size(); i++)
    request << headers_[i] << "\r\n";
  request << "Content-Length: " << size << "\r\nConnection: close\r\n\r\n";
  request.write(reinterpret_cast<const char *>(payload), static_cast<std::streamsize>(size));
  const std::string bytes = request.str();
  if (send(fd, bytes.data(), bytes.size(), 0) != static_cast<ssize_t>(bytes.size()))
  {
    close(fd);
    return HTTPC_ERROR_SEND_PAYLOAD_FAILED;
  }
  std::string response;
  char chunk[1024];
  for (;;)
  {
    const ssize_t n = recv(fd, chunk, sizeof(chunk), 0);
    if (n > 0)
    {
      response.append(chunk, static_cast<size_t>(n));
      continue;
    }
    if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK) && response.empty())
    {
      close(fd);
      return HTTPC_ERROR_READ_TIMEOUT;
    }
    break;
  }
  close(fd);
  const size_t split = response.find("\r\n\r\n");
  if (response.compare(0, 9, "HTTP/1.1 ") != 0 || split == std::string::npos)
  {
    return HTTPC_ERROR_READ_TIMEOUT;
  }
  body_ = response.substr(split + 4);
  status_ = atoi(response.c_str() + 9);
  std::string head = response.substr(0, split);
  for (size_t i = 0; i < head.size(); i++)
    head[i] = static_cast<char>(tolower(head[i]));
  bodyUntilClose_ = head.find("\r\ncontent-length:") == std::string::npos &&
                    head.find("\r\ntransfer-encoding:") == std::string::npos;
  return status_;
}

// This fake closes every connection, so it always has the whole body. The real one
// keeps the connection open (setReuse) and, for a reply with no length, reads until the
// server closes it: about a minute behind nginx, with the clicker frozen meanwhile.
// That is reported here so e2e_test.py can fail on it.
String HTTPClient::getString(void)
{
  if (reuse_ && bodyUntilClose_)
  {
    ::printf("SIM HTTPClient trap: getString() on HTTP %d with no length would wait "
             "for the server to close the connection\n",
             status_);
    fflush(stdout);
  }
  return String(body_);
}
