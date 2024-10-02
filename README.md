# KOPIS_custom

Version: 1.0.1

> **BASE URL** > **[ruehan-kopis.org](https://ruehan-kopis.org)**

## Get Performances

`GET /performances`

## 공연목록 조회 API

### Parameters

- `stdate` (query) (Required): 공연시작일자
- `eddate` (query) (Required): 공연종료일자
- `cpage` (query): 현재페이지
- `rows` (query): 페이지당 목록 수
- `shprfnm` (query): 공연명
- `shprfnmfct` (query): 공연시설명
- `shcate` (query): 장르코드
- `prfplccd` (query): 공연장코드
- `signgucode` (query): 지역(시도)코드
- `signgucodesub` (query): 지역(구군)코드
- `kidstate` (query): 아동공연여부
- `prfstate` (query): 공연상태코드
- `openrun` (query): 오픈런

### Responses

- **200**: Successful Response
- **422**: Validation Error

---

## Get Upcoming Performances

`GET /upcoming-performances`

## 공연 예정 목록 조회 API

### Responses

- **200**: Successful Response

---

## Get Performance Detail

`GET /performance/{mt20id}`

## 공연상세정보 조회 API

### Parameters

- `mt20id` (path) (Required):

### Responses

- **200**: Successful Response
- **422**: Validation Error

---

## Get Auto Fill

`GET /auto-fill`

## 자동완성 API

### Parameters

- `stdate` (query) (Required): 공연시작일자
- `eddate` (query) (Required): 공연종료일자
- `cpage` (query): 현재페이지
- `rows` (query): 페이지당 목록 수
- `shprfnm` (query) (Required): 공연명

### Responses

- **200**: Successful Response
- **422**: Validation Error

---

## Update Facilities

`POST /update-facilities`

## 사용금지!!

## 공연시설 DB 업데이트

### Parameters

- `signgucode` (query): 지역(시도)코드

### Responses

- **200**: Successful Response
- **422**: Validation Error

---

## Get Performance Facilities

`GET /performance-facilities`

공연시설 조회 API

### Parameters

- `signgucode` (query): 지역(시도)코드
- `signgucodesub` (query): 지역(구군)코드
- `fcltychartr` (query): 공연시설특성코드
- `shprfnmfct` (query): 공연시설명
- `cpage` (query): 현재페이지
- `rows` (query): 페이지당 목록 수

### Responses

- **200**: Successful Response
- **422**: Validation Error

---

## Get Popular By Genre

`GET /popular-by-genre`

## 장르별로 공연 1개 반환

### stdate / eddate 수정 필요!

### Responses

- **200**: Successful Response

---

## Get User Picks

`GET /user-picks`

## Token 기반 사용자 공연 Pick 반환

### Responses

- **200**: Successful Response

---

## Save User Picks

`POST /user-picks`

## Token 기반 사용자 공연 Pick 저장

### Request Body

Content type: `application/json`

### Responses

- **200**: Successful Response
- **422**: Validation Error

---

## Generate Token

`POST /token`

### Responses

- **200**: Successful Response

---

## Get Recommended Shows

`GET /recommended-shows`

## 공연 Pick에 따른 추천 공연 리스트

### Responses

- **200**: Successful Response

---

## Drop Upcoming Performance Table

`DELETE /upcoming-performances/drop`

Delete the entire upcoming_performances table.

### Responses

- **200**: Successful Response

---

## Root

`GET /`

### Responses

- **200**: Successful Response

---

## Get Markdown Docs

`GET /docs/markdown`

API 문서를 간결한 Markdown 형식으로 반환

### Responses

- **200**: Successful Response

---
