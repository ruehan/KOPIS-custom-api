# KOPIS-custom

Version: 0.1.0

> **BASE URL** > **[ruehan-kopis.org](https://ruehan-kopis.org)**

## GET /performances

## 공연목록 조회 API

### Parameters

| Name          | Located in | Description      | Required | Schema  |
| ------------- | ---------- | ---------------- | -------- | ------- |
| stdate        | query      | 공연시작일자     | True     | string  |
| eddate        | query      | 공연종료일자     | True     | string  |
| cpage         | query      | 현재페이지       | False    | integer |
| rows          | query      | 페이지당 목록 수 | False    | integer |
| shprfnm       | query      | 공연명           | False    |         |
| shprfnmfct    | query      | 공연시설명       | False    |         |
| shcate        | query      | 장르코드         | False    |         |
| prfplccd      | query      | 공연장코드       | False    |         |
| signgucode    | query      | 지역(시도)코드   | False    |         |
| signgucodesub | query      | 지역(구군)코드   | False    |         |
| kidstate      | query      | 아동공연여부     | False    |         |
| prfstate      | query      | 공연상태코드     | False    |         |
| openrun       | query      | 오픈런           | False    |         |

### Responses

**200**

Successful Response

Content type: application/json

Schema:

```json
{
	"type": "array",
	"items": {
		"$ref": "#/components/schemas/Performance"
	},
	"title": "Response Get Performances Performances Get"
}
```

**422**

Validation Error

Content type: application/json

Schema:

```json
{
	"$ref": "#/components/schemas/HTTPValidationError"
}
```

---

## GET /performance/{mt20id}

## 공연상세정보 조회 API

### Parameters

| Name   | Located in | Description | Required | Schema |
| ------ | ---------- | ----------- | -------- | ------ |
| mt20id | path       |             | True     | string |

### Responses

**200**

Successful Response

Content type: application/json

Schema:

```json
{
	"$ref": "#/components/schemas/PerformanceDetail"
}
```

**422**

Validation Error

Content type: application/json

Schema:

```json
{
	"$ref": "#/components/schemas/HTTPValidationError"
}
```

---

## GET /performance-facilities

공연시설 조회 API

### Parameters

| Name          | Located in | Description      | Required | Schema  |
| ------------- | ---------- | ---------------- | -------- | ------- |
| signgucode    | query      | 지역(시도)코드   | False    |         |
| signgucodesub | query      | 지역(구군)코드   | False    |         |
| fcltychartr   | query      | 공연시설특성코드 | False    |         |
| shprfnmfct    | query      | 공연시설명       | False    |         |
| cpage         | query      | 현재페이지       | False    | integer |
| rows          | query      | 페이지당 목록 수 | False    | integer |

### Responses

**200**

Successful Response

Content type: application/json

Schema:

```json
{
	"type": "array",
	"items": {
		"$ref": "#/components/schemas/PerformanceFacility"
	},
	"title": "Response Get Performance Facilities Performance Facilities Get"
}
```

**422**

Validation Error

Content type: application/json

Schema:

```json
{
	"$ref": "#/components/schemas/HTTPValidationError"
}
```

---

## GET /docs/markdown

API 문서를 Markdown 형식으로 반환

### Responses

**200**

Successful Response

Content type: text/plain

Schema:

```json
{
	"type": "string"
}
```

---
