# 📡 支持统计内容(Statistical content)

## Zoomeye

### 主机搜索 (Host Search)

|    统计项     |   类型   |   说明   |
|:----------:|:------:|:------:|
|     ip     | String |  ip地址  |
|    port    | String |   端口   |
|     os     | String |  操作系统  |
|    app     | String | 应用、设备等 |
|  version   | String | 应用版本号  |
|   title    | String |   标题   |
|    city    | String |   城市   |
|  country   | String |   国家   |
| continents | String |   大洲   |

### 域名/IP (Domain/IP)

| 统计项  |   类型   |  说明  |
|:----:|:------:|:----:|
|  ip  | String | ip地址 |
| name | String |  域名  |

### web应用搜索 (web application search)

|    统计项    |   类型   |   说明    |
|:---------:|:------:|:-------:|
|    ip     | String |  ip地址   |
|   site    | String |   站点    |
|   title   | String |  网站标题   |
|   city    | String |   城市    |
|  country  | String |   国家    |
| continent | String |   大洲    |
|    isp    | String | 网络服务提供商 |

---

## Fofa

|       统计项       |   类型   |    说明    |
|:---------------:|:------:|:--------:|
|       ip        | String |   ip地址   |
|      port       | String |    端口    |
|    protocol     | String |   协议名    |
|  country_name   | String |   国家名    |
|     region      | String |    地区    |
|      city       | String |    城市    |
| as_organization | String |  asn组织   |
|      host       | String |   主机名    |
|     domain      | String |    域名    |
|       os        | String |   操作系统   |
|     server      | String | 网站server |
|       icp       | String |  icp备案号  |
|      title      | String |   网站标题   |
|      jarm       | String |  jarm指纹  |

---

## Quake

### 主机数据查询 (Host)

|       统计项        |   类型   |   说明    |
|:----------------:|:------:|:-------:|
|        ip        | String |  ip地址   |
|   service_port   | String |  服务端口   |
|   service_name   | String |   服务名   |
| service_versioin | String |  服务版本   |
|    service_id    | String |  服务id   |
|     domains      | String |   域名    |
|     hostname     | String |   主机名   |
|     os_name      | String |   系统名   |
|    os_version    | String |  系统版本   |
|    country_en    | String | 国家名(En) |
|     city_en      | String | 城市名(En) |

### 服务数据查询 (Service)

|      统计项       |   类型   |   说明    |
|:--------------:|:------:|:-------:|
|       ip       | String |  ip地址   |
|      port      | String |   端口    |
|      org       | String |   组织名   |
|    hostname    | String |   主机名   |
|  service_name  | String |  服务名称   |
| service_title  | String |  服务标题   |
| service_server | String |  服务服务器  |
|   transport    | String |   协议    |
|    os_name     | String |  操作系统名  |
|   country_en   | String | 国家名(En) |
|    city_en     | String | 城市名(En) |
|   os_version   | String |  系统版本   |

---

## Shodan

|    统计项    |   类型   |   说明    |
|:---------:|:------:|:-------:|
|    ip     | String |  ip地址   |
|   port    | String |   端口    |
|  domains  | String |   域名    |
|   title   | String |   标题    |
|  product  | String |  软件或产品  |
|    os     | String |   系统    |
|   info    | String | 产品相关信息  |
|    isp    | String | 网络服务提供商 |
|  country  | String |   国家    |
|   city    | String |   城市    |
| timestamp | String |   时间戳   |

## Hunter

|       字段名        |   类型    |   描述    |
|:----------------:|:-------:|:-------:|
|       url        | String  |  URL地址  |
|        ip        | String  |  IP地址   |
|       port       | String  |   端口号   |
|    web_title     | String  |  网页标题   |
|      domain      | String  | 域名或域名列表 |
| is_risk_protocol | Boolean | 是否为风险协议 |
|     protocol     | String  |   协议    |
|  base_protocol   | String  |  基础协议   |
|   status_code    | String  |   状态码   |
|    component     | String  | 组件或组件列表 |
|        os        | String  |  操作系统   |
|     company      | String  |   公司    |
|      number      | String  |   号码    |
|     country      | String  |   国家    |
|     province     | String  |   省份    |
|       city       | String  |   城市    |
|    updated_at    | String  |  更新时间   |
|      is_web      | Boolean |  是否为网页  |
|      as_org      | String  |  AS组织   |
|       isp        | String  | ISP提供商  |
|     vul_list     | String  |  漏洞列表   |
|     is_risk      | Boolean |  是否为风险  |