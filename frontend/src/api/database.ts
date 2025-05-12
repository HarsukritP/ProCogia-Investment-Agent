// This file would contain utility functions for interacting with databases
// such as MongoDB, Redis, InfluxDB, etc.

import apiClient from './index';

// MongoDB connection (via backend proxy API)
export const fetchDocuments = async (collection: string, query: any = {}, limit: number = 100) => {
  try {
    const response = await apiClient.post('/db/query', {
      collection,
      query,
      limit
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching documents:', error);
    throw error;
  }
};

// Redis cache operations
export const getCachedData = async (key: string) => {
  try {
    const response = await apiClient.get(`/cache/${key}`);
    return response.data;
  } catch (error) {
    console.error('Error getting cached data:', error);
    return null;
  }
};

export const setCachedData = async (key: string, value: any, expiry?: number) => {
  try {
    const response = await apiClient.post('/cache', {
      key,
      value,
      expiry
    });
    return response.data;
  } catch (error) {
    console.error('Error setting cached data:', error);
    throw error;
  }
};

// InfluxDB time series data operations
export const fetchTimeSeriesData = async (measurement: string, start: string, end: string, tags: Record<string, string> = {}) => {
  try {
    const response = await apiClient.post('/timeseries/query', {
      measurement,
      start,
      end,
      tags
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching time series data:', error);
    throw error;
  }
};