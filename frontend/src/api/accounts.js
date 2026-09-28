import { api } from './client'

export function getCurrentPlayer() {
  return api.get('/accounts/me/')
}

export function login(username, password) {
  return api.post('/accounts/login/', {
    username,
    password,
  })
}

export function logout() {
  return api.post('/accounts/logout/')
}