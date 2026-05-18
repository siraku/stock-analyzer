import client from './client'
import { PortfolioAnalysis } from '@/types/portfolio'

export async function analyzePortfolio(filePath: string): Promise<PortfolioAnalysis> {
  const { data } = await client.post<PortfolioAnalysis>('/portfolio/analyze', {
    file_path: filePath,
  })
  return data
}

export async function renameGroup(oldName: string, newName: string): Promise<void> {
  await client.patch('/portfolio/groups/rename', { old_name: oldName, new_name: newName })
}

export async function reassignTicker(ticker: string, groupName: string): Promise<void> {
  await client.patch(`/portfolio/groups/${ticker}`, { group_name: groupName })
}
