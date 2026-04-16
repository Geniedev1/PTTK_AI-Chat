import axios from "axios"

const flattenValue = (value: unknown): string[] => {
  if (typeof value === "string") {
    return [value]
  }
  if (Array.isArray(value)) {
    return value.flatMap(flattenValue)
  }
  if (value && typeof value === "object") {
    return Object.values(value).flatMap(flattenValue)
  }
  return []
}

export const getApiErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const payload = error.response?.data as unknown
    if (payload && typeof payload === "object") {
      const detail = (payload as { detail?: unknown }).detail
      if (typeof detail === "string" && detail.trim()) {
        return detail
      }

      const message = (payload as { message?: unknown }).message
      if (typeof message === "string" && message.trim()) {
        return message
      }

      const collected = flattenValue(payload).filter((item) => item.trim())
      if (collected.length > 0) {
        const first = collected[0]
        if (first) {
          return first
        }
      }
    }

    if (typeof error.message === "string" && error.message.trim()) {
      return error.message
    }
  }

  return "Unexpected error. Please try again."
}