# KOPIS_custom

Version: 1.0.0

> **BASE URL** > **[ruehan-kopis.org](https://ruehan-kopis.org)**

## 공연목록 조회 API

`GET /performances`

### Parameters

- `stdate` (query): 공연시작일자
  - Type: `string`
  - Required: Yes
- `eddate` (query): 공연종료일자
  - Type: `string`
  - Required: Yes
- `cpage` (query): 현재페이지
  - Type: `integer`
- `rows` (query): 페이지당 목록 수
  - Type: `integer`
- `shprfnm` (query): 공연명
  - Type: ``
- `shprfnmfct` (query): 공연시설명
  - Type: ``
- `shcate` (query): 장르코드
  - Type: ``
- `prfplccd` (query): 공연장코드
  - Type: ``
- `signgucode` (query): 지역(시도)코드
  - Type: ``
- `signgucodesub` (query): 지역(구군)코드
  - Type: ``
- `kidstate` (query): 아동공연여부
  - Type: ``
- `prfstate` (query): 공연상태코드
  - Type: ``
- `openrun` (query): 오픈런
  - Type: ``

---

## 공연상세정보 조회 API

`GET /performance/{mt20id}`

### Parameters

- `mt20id` (path):
  - Type: `string`
  - Required: Yes

---

## 자동완성 API

`GET /auto-fill`

### Parameters

- `cpage` (query): 현재페이지
  - Type: `integer`
- `rows` (query): 페이지당 목록 수
  - Type: `integer`
- `shprfnm` (query): 공연명
  - Type: `string`
  - Required: Yes

---

## 공연시설 DB 업데이트

`POST /update-facilities`

## 사용금지!!

### Parameters

- `signgucode` (query): 지역(시도)코드
  - Type: ``

---

`GET /performance-facilities`

공연시설 조회 API

### Parameters

- `signgucode` (query): 지역(시도)코드
  - Type: ``
- `signgucodesub` (query): 지역(구군)코드
  - Type: ``
- `fcltychartr` (query): 공연시설특성코드
  - Type: ``
- `shprfnmfct` (query): 공연시설명
  - Type: ``
- `cpage` (query): 현재페이지
  - Type: `integer`
- `rows` (query): 페이지당 목록 수
  - Type: `integer`

---

## Get Markdown Docs

`GET /docs/markdown`

API 문서를 ReDoc 스타일의 Markdown 형식으로 반환

---
