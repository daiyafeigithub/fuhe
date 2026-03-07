/**
 * API 字段映射工具
 * 将前端驼峰命名转换为后端下划线命名
 */

const camelToSnake = (str) => {
  return str.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
}

const snakeToCamel = (str) => {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

const isPlainObject = (value) => {
  if (!value || Object.prototype.toString.call(value) !== '[object Object]') {
    return false
  }
  const prototype = Object.getPrototypeOf(value)
  return prototype === Object.prototype || prototype === null
}

const isSpecialObject = (value) => {
  if (value instanceof Date) return true
  if (typeof FormData !== 'undefined' && value instanceof FormData) return true
  if (typeof Blob !== 'undefined' && value instanceof Blob) return true
  if (typeof File !== 'undefined' && value instanceof File) return true
  if (typeof URLSearchParams !== 'undefined' && value instanceof URLSearchParams) return true
  return false
}

export const transformRequest = (data) => {
  if (Array.isArray(data)) {
    return data.map(item => transformRequest(item))
  }

  if (isSpecialObject(data) || !isPlainObject(data)) {
    return data
  }

  const transformed = {}
  for (const key in data) {
    const snakeKey = camelToSnake(key)
    transformed[snakeKey] = transformRequest(data[key])
  }
  return transformed
}

export const transformResponse = (data) => {
  if (Array.isArray(data)) {
    return data.map(item => transformResponse(item))
  }

  if (isSpecialObject(data) || !isPlainObject(data)) {
    return data
  }

  const transformed = {}
  for (const key in data) {
    const camelKey = snakeToCamel(key)
    transformed[camelKey] = transformResponse(data[key])
  }
  return transformed
}

// 特殊的字段映射（需要自定义的字段名转换）
export const specialMappings = {
  qrcode: {
    request: {
      enterpriseCode: 'enterprise_code',
      cjId: 'cj_id',
      batchNo: 'batch_no'
    },
    response: {
      qrcodeId: 'qrcode_id',
      qrcodeContent: 'qrcode_content',
      base64Str: 'base64_str',
      qrcodeUrl: 'qrcode_url',
      batchNo: 'batch_no'
    }
  }
}
