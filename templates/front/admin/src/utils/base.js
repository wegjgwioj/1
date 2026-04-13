export const apiBaseUrl = import.meta.env?.VITE_API_BASE_URL || 'http://127.0.0.1:8082'
const base = {
  get() {
    return {
      url: apiBaseUrl + '/diandong5k56la1f/',
      name: 'diandong5k56la1f',
      frontUrl: '',
    }
  },
}
export default base
