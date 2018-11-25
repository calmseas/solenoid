# Eureka Client for Python

```yaml
instance:
  instanceId: localhost:testclient:7091
  hostName: localhost
  app: testclient
  ipAddr: 127.0.0.1
  vipAddress: testclient
  secureVipAddress: testclient
  status: UP
  port:
    $: 7091
    '@enabled': true
  securePort:
    $: 443
    '@enabled': false
  statusPageUrl: http://localhost:7091/info
  statusPagePath: /info
  homePageUrl: http://localhost:7091/
  homePagePath: /
  healthCheckUrl: http://localhost:7091/health
  healthCheckPath: /health
  dataCenterInfo:
    '@class': com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo
    name: MyOwn

eureka:
  host: localhost
  port: 8080
  ssl: false
  servicePath: /eureka/apps
  
options:
  requestImpl: requests
  maxRetries: 3
  heartBeatIntervalInSecs: 30
  registryFetchIntervalInSecs: 30
  registerWithEureka: true

```
