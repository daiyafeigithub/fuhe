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

export const transformRequest = (data) => {
  if (!data || typeof data !== 'object') return data

  const transformed = {}
  for (const key in data) {
    const snakeKey = camelToSnake(key)
    transformed[snakeKey] = data[key]
  }
  return transformed
}

export const transformResponse = (data) => {
  if (!data || typeof data !== 'object') return data

  if (Array.isArray(data)) {
    return data.map(item => transformResponse(item))
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
