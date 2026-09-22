import { describe, expect, it, vi } from 'vitest';
import * as httpClient from '../../../shared/api/httpClient';
import { bankApi } from '../bankApi';
import { question } from './bankFixture';

describe('bankApi', () => {
  it('listQuestions defaults to 5 rows per page', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ questions: [], total: 0 });
    await bankApi.listQuestions({ topic: 'sumas', offset: 0 });
    expect(spy).toHaveBeenCalledWith(
      'GET',
      '/quiz/questions?topic=sumas&limit=5&offset=0'
    );
    spy.mockRestore();
  });

  it('validateQuestion posts the question envelope', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ is_valid: true, errors: [], details: {} });
    await bankApi.validateQuestion(question);
    expect(spy).toHaveBeenCalledWith('POST', '/quiz/validate', {
      question,
    });
    spy.mockRestore();
  });

  it('deleteQuestion sends DELETE', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({});
    await bankApi.deleteQuestion('q1');
    expect(spy).toHaveBeenCalledWith('DELETE', '/quiz/questions/q1');
    spy.mockRestore();
  });

  it('updateQuestion sends PUT', async () => {
    const spy = vi
      .spyOn(httpClient, 'requestApi')
      .mockResolvedValue({ ...question });
    await bankApi.updateQuestion('q1', { ...question, id: 'q1' });
    expect(spy).toHaveBeenCalledWith(
      'PUT',
      '/quiz/questions/q1',
      expect.objectContaining({ id: 'q1' })
    );
    spy.mockRestore();
  });

  it('getSchema fetches the contract', async () => {
    const spy = vi.spyOn(httpClient, 'requestApi').mockResolvedValue({});
    await bankApi.getSchema();
    expect(spy).toHaveBeenCalledWith('GET', '/quiz/schema');
    spy.mockRestore();
  });
});
