import { api } from './client'

export function getStandings() {
  return api.get('/league/standings/')
}

export function getCurrentWeek() {
  return api.get('/league/current-week/')
}