/**
 * StrategiesPage.tsx  T16.7 ✅
 */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Cpu, Play, Pause, Plus, Trash2 } from 'lucide-react'
import { strategyService } from '@/services'
import { Card, Badge, Button, Spinner, EmptyState, Table, Tr, Td } from '@/components/ui'
import toast from 'react-hot-toast'

export function StrategiesPage() {
  const qc = useQueryClient()
  const [activeTab, setActiveTab] = useState<'mine' | 'library'>('mine')

  const { data: myStrats, isLoading: myLoad }  = useQuery({ queryKey: ['my-strategies'], queryFn: () => strategyService.list() })
  const { data: library,  isLoading: libLoad } = useQuery({ queryKey: ['strategy-library'], queryFn: () => strategyService.library() })

  const activateMutation   = useMutation({ mutationFn: (id: string) => strategyService.activate(id),   onSuccess: () => { qc.invalidateQueries({ queryKey: ['my-strategies'] }); toast.success('Strategy activated.') } })
  const deactivateMutation = useMutation({ mutationFn: (id: string) => strategyService.deactivate(id), onSuccess: () => { qc.invalidateQueries({ queryKey: ['my-strategies'] }); toast.success('Strategy deactivated.') } })
  const deleteMutation     = useMutation({ mutationFn: (id: string) => strategyService.delete(id),     onSuccess: () => { qc.invalidateQueries({ queryKey: ['my-strategies'] }); toast.success('Strategy removed.') } })

  const myList  = (myStrats?.data?.data || []) as any[]
  const libList = (library?.data?.data  || []) as any[]

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Cpu size={18} className="text-brand-400" />
          <h1 className="text-lg font-semibold text-neutral-100">Strategies</h1>
        </div>
        <Button size="sm"><Plus size={13} /> Add Strategy</Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-neutral-800 p-1 rounded-lg w-fit border border-neutral-700">
        {[['mine','My Strategies'],['library','Strategy Library']].map(([v,l]) => (
          <button key={v} onClick={() => setActiveTab(v as any)}
            className={`px-3 py-1.5 text-sm rounded-md transition-colors ${activeTab === v ? 'bg-brand-600 text-white' : 'text-neutral-400 hover:text-neutral-100'}`}>
            {l}
          </button>
        ))}
      </div>

      {activeTab === 'mine' && (
        <Card>
          {myLoad
            ? <div className="flex justify-center py-12"><Spinner /></div>
            : myList.length === 0
              ? <EmptyState icon={<Cpu size={28} />} title="No strategies yet" message="Add a strategy from the library." action={<Button size="sm" onClick={() => setActiveTab('library')}><Plus size={13} /> Browse Library</Button>} />
              : <Table headers={['Strategy', 'Type', 'Automation', 'Min Confidence', 'Mode', 'Status', 'Actions']}>
                  {myList.map((s: any) => (
                    <Tr key={s.id}>
                      <Td className="font-medium text-neutral-100">{s.name}</Td>
                      <Td><Badge variant="default">{s.strategy_type}</Badge></Td>
                      <Td><Badge variant={s.automation_level === 'FULL_AUTO' ? 'success' : 'warning'}>{s.automation_level}</Badge></Td>
                      <Td className="trading-value">{s.min_confidence_score}</Td>
                      <Td>{s.is_paper_mode ? <Badge variant="warning">PAPER</Badge> : <Badge variant="success">LIVE</Badge>}</Td>
                      <Td>{s.is_active ? <Badge variant="success">ACTIVE</Badge> : <Badge variant="default">INACTIVE</Badge>}</Td>
                      <Td>
                        <div className="flex items-center gap-1">
                          {s.is_active
                            ? <Button size="sm" variant="secondary" loading={deactivateMutation.isPending} onClick={() => deactivateMutation.mutate(s.id)}><Pause size={11} /></Button>
                            : <Button size="sm" variant="secondary" loading={activateMutation.isPending}   onClick={() => activateMutation.mutate(s.id)}><Play size={11} /></Button>
                          }
                          <Button size="sm" variant="ghost" onClick={() => { if (confirm('Remove strategy?')) deleteMutation.mutate(s.id) }}>
                            <Trash2 size={11} className="text-danger" />
                          </Button>
                        </div>
                      </Td>
                    </Tr>
                  ))}
                </Table>
          }
        </Card>
      )}

      {activeTab === 'library' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {libLoad
            ? <div className="col-span-3 flex justify-center py-12"><Spinner /></div>
            : libList.map((s: any) => (
                <Card key={s.id} className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-sm font-semibold text-neutral-100">{s.name}</h3>
                      <Badge variant="default" className="mt-1">{s.strategy_type}</Badge>
                    </div>
                    {s.requires_premium && <Badge variant="warning">PREMIUM</Badge>}
                  </div>
                  <p className="text-xs text-neutral-400 mb-3 leading-relaxed">{s.description}</p>
                  <div className="text-xs text-neutral-500 mb-3">
                    Suitable: {(s.suitable_regimes || []).slice(0,2).join(', ')}
                  </div>
                  <Button size="sm" variant="secondary" className="w-full">
                    <Plus size={12} /> Use Strategy
                  </Button>
                </Card>
              ))
          }
        </div>
      )}
    </div>
  )
}
