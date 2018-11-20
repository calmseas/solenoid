# Eureka Client for Python

```yaml
instance:
  instanceId: localhost:testclient:8080
  hostName: localhost
  app: testclient
  ipAddr: 127.0.0.1
  vipAddress: testclient
  secureVipAddress: testclient
  status: UP
  port:
    $: 8080
    '@enabled': 'true'
  securePort:
    $: 443
    '@enabled': 'false'
  statusPageUrl: http://localhost:8080/info
  homePageUrl: None
  healthCheckUrl: None
  dataCenterInfo:
    '@class': com.netflix.appinfo.InstanceInfo$DefaultDataCenterInfo
    name: MyOwn

eureka:
  host: localhost
  port: 9091
  ssl: false
  servicePath: /eureka/apps/
  
options:
  requestImpl: requests
  maxRetries: 3
  heartBeatIntervalInSecs: 30
  registryFetchIntervalInSecs: 30
  registerWithEureka: true

```
