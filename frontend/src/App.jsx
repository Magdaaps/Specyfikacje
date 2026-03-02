import React, { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import {
  Package,
  Database,
  Settings,
  Search,
  Plus,
  X,
  Download,
  Cloud,
  ChevronRight,
  Info,
  AlertTriangle,
  FileSpreadsheet,
  ArrowLeft,
  FolderPlus
} from 'lucide-react'
import ProductDetails from './ProductDetails'
import AddProductModal from './AddProductModal'
import AddSurowiecModal from './AddSurowiecModal'
import Notification from './Notification'
import logo from './assets/logo.png'

const API_BASE = import.meta.env.VITE_API_BASE || ""

// Stała kolejność kategorii i ich polskie etykiety
const PRODUCT_TYPE_ORDER = ['lizaki', 'figurki', 'tabliczki', 'inne']
const PRODUCT_TYPE_LABELS = {
  lizaki: 'Lizaki',
  figurki: 'Figurki',
  tabliczki: 'Tabliczki',
  inne: 'Inne',
}

function ProductCard({ item, onClick }) {
  const [imgFailed, setImgFailed] = useState(false)
  const imageUrl = item.image_url
    ? (item.image_url.startsWith('http') ? item.image_url : `${API_BASE}${item.image_url}`)
    : null
  const showImage = imageUrl && !imgFailed

  return (
    <div
      onClick={() => onClick(item.ean || '~')}
      className="bg-white border border-choco-100 rounded-3xl overflow-hidden hover:border-gold-500/50 hover:shadow-2xl hover:shadow-choco-900/15 transition-all group cursor-pointer shadow-sm flex flex-col"
    >
      {/* Image Section */}
      <div className="aspect-[4/3] relative overflow-hidden">
        {showImage ? (
          <>
            <div className="absolute inset-0 bg-choco-50/50" />
            <div className="absolute inset-0 bg-gradient-to-t from-choco-900/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity z-10" />
            <div className="absolute inset-0 flex items-center justify-center p-6 z-20">
              <img
                src={imageUrl}
                alt={item.nazwa_pl}
                className="max-w-full max-h-full object-contain transform group-hover:scale-105 transition-transform duration-500 drop-shadow-md"
                onError={() => setImgFailed(true)}
              />
            </div>
          </>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center p-5" style={{ background: '#7d5c4f' }}>
            <span className="text-white text-xs font-semibold text-center leading-relaxed line-clamp-4">{item.nazwa_pl}</span>
          </div>
        )}
        <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-full shadow-lg z-30">
          <span className="text-[10px] font-black text-choco-800 uppercase tracking-widest">ID: {item.ean ? item.ean.slice(-6) : '—'}</span>
        </div>
      </div>

      {/* Content Section */}
      <div className="p-6 flex flex-col flex-1">
        <div className="flex-1">
          <p className="text-gold-600 font-black text-[9px] uppercase tracking-[0.2em] mb-2">Specyfikacja Wyrobu</p>
          <h3 className="font-bold text-lg text-choco-900 group-hover:text-choco-700 transition-colors uppercase tracking-tight leading-snug line-clamp-2 min-h-[3rem]">
            {item.nazwa_pl}
          </h3>
        </div>

        <div className="mt-6 pt-5 border-t border-choco-50 flex items-center justify-between gap-3">
          <div className="flex flex-col min-w-0">
            <span className="text-choco-300 uppercase tracking-widest text-[9px] font-bold">Kod EAN</span>
            <span className="text-choco-700 font-mono font-bold text-xs tracking-wider">{item.ean}</span>
          </div>
          <div className="bg-choco-50 border border-choco-100 px-3 py-1.5 rounded-xl flex-shrink-0 max-w-[130px]">
            <span className="text-[10px] font-black text-choco-500 uppercase tracking-wide block truncate whitespace-nowrap">
              {item.kategoria || '—'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [activeTab, setActiveTab] = useState('produkty')
  const [produkty, setProdukty] = useState([])
  const [surowce, setSurowce] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(false)
  const [selectedProductEan, setSelectedProductEan] = useState(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [addModalProductType, setAddModalProductType] = useState('inne')
  const [selectedProductType, setSelectedProductType] = useState('lizaki')
  const [selectedKategoria, setSelectedKategoria] = useState('')
  const [showAddSurowiecModal, setShowAddSurowiecModal] = useState(false)
  const [editingSurowiec, setEditingSurowiec] = useState(null)
  const [notification, setNotification] = useState(null)

  // New state for categories
  const [selectedCategory, setSelectedCategory] = useState(null)

  useEffect(() => {
    // Keep Render backend alive (free tier sleeps after 15 min inactivity)
    const keepAlive = () => axios.get(`${API_BASE}/`).catch(() => { })
    keepAlive()
    const timer = setInterval(keepAlive, 9 * 60 * 1000) // every 9 min
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    // Setup Axios Interceptor
    const interceptor = axios.interceptors.response.use(
      response => response,
      error => {
        const data = error.response?.data
        const detail422 = Array.isArray(data?.detail) ? `[${data.detail[0]?.loc?.slice(1).join('.')}] ${data.detail[0]?.msg}` : null
        const message = data?.error || detail422 || error.message || "Wystąpił nieoczekiwany błąd"
        setNotification({ message, type: 'error' })
        return Promise.reject(error)
      }
    )
    return () => axios.interceptors.response.eject(interceptor)
  }, [])

  useEffect(() => {
    fetchData()
  }, [activeTab])

  const fetchData = async () => {
    setLoading(true)
    try {
      const endpoint = activeTab === 'produkty' ? '/produkty' : '/surowce'
      const res = await axios.get(`${API_BASE}${endpoint}`)
      if (activeTab === 'produkty') setProdukty(Array.isArray(res.data) ? res.data : [])
      else setSurowce(Array.isArray(res.data) ? res.data : [])
    } catch (err) {
      console.error("Error fetching data:", err)
    } finally {
      setLoading(false)
    }
  }

  // Categories calculation for surowce
  const categories = useMemo(() => {
    const cats = {}
    surowce.forEach(s => {
      const cat = s.kategoria || 'Inne'
      cats[cat] = (cats[cat] || 0) + 1
    })
    return Object.entries(cats).map(([name, count]) => ({ name, count })).sort((a, b) => a.name.localeCompare(b.name))
  }, [surowce])

  // Produkty grouped by product_type (for catalog view)
  const produktyByType = useMemo(() => {
    const groups = {}
    PRODUCT_TYPE_ORDER.forEach(t => { groups[t] = [] })
    produkty.forEach(p => {
      const t = p.product_type || 'inne'
      if (!groups[t]) groups[t] = []
      groups[t].push(p)
    })
    return groups
  }, [produkty])

  // Filtered produkty for search
  const filteredProdukty = useMemo(() => {
    if (!searchTerm) return null
    return produkty.filter(item =>
      (item.nazwa_pl || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.ean || "").includes(searchTerm)
    )
  }, [produkty, searchTerm])

  // Products in active tab, optionally filtered by kategoria
  const filteredTabItems = useMemo(() => {
    const base = produktyByType[selectedProductType] || []
    if (!selectedKategoria) return base
    return base.filter(p => (p.kategoria || '') === selectedKategoria)
  }, [produktyByType, selectedProductType, selectedKategoria])

  const filteredSurowce = useMemo(() => {
    if (activeTab !== 'surowce') return []
    if (searchTerm) {
      return surowce.filter(item =>
        (item.nazwa || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.kategoria || "").toLowerCase().includes(searchTerm.toLowerCase())
      )
    }
    if (selectedCategory) {
      return surowce.filter(item => (item.kategoria || 'Inne') === selectedCategory)
    }
    return []
  }, [activeTab, surowce, searchTerm, selectedCategory])

  const handleAddCategory = () => {
    const name = prompt("Podaj nazwę nowej kategorii:")
    if (name) {
      setEditingSurowiec({ kategoria: name, nazwa: '' })
      setShowAddSurowiecModal(true)
    }
  }

  const openAddProductModal = (productType = 'inne') => {
    setAddModalProductType(productType)
    setShowAddModal(true)
  }

  const totalProdukty = produkty.length

  return (
    <div className="flex h-screen bg-choco-50 text-choco-900 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-choco-100 flex flex-col p-6 shadow-xl">
        <div className="flex flex-col items-center gap-2 mb-10 px-2">
          <img src={logo} alt="Adikam Logo" className="w-32 h-auto drop-shadow-md" />
          <h1 className="font-black text-xs uppercase tracking-[0.3em] text-choco-800 mt-2">Specyfikacje</h1>
        </div>

        <nav className="space-y-2 flex-1">
          <button
            onClick={() => {
              setActiveTab('produkty')
              setSearchTerm('')
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'produkty' ? 'bg-choco-800 text-white shadow-lg shadow-choco-900/40' : 'text-choco-600 hover:bg-choco-50'}`}
          >
            <Package className="w-5 h-5" />
            <span className="font-medium">Produkty</span>
          </button>
          <button
            onClick={() => {
              setActiveTab('surowce')
              setSearchTerm('')
              setSelectedCategory(null)
            }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${activeTab === 'surowce' ? 'bg-choco-800 text-white shadow-lg shadow-choco-900/40' : 'text-choco-600 hover:bg-choco-50'}`}
          >
            <Database className="w-5 h-5" />
            <span className="font-medium">Baza Surowców</span>
          </button>
        </nav>

        <div className="mt-auto pt-6 border-t border-choco-100 space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-choco-500 hover:bg-choco-50 transition-all">
            <Cloud className="w-5 h-5 text-gold-600" />
            <span className="font-medium">SharePoint</span>
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-choco-500 hover:bg-choco-50 transition-all">
            <Settings className="w-5 h-5" />
            <span className="font-medium">Ustawienia</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden bg-choco-100/30">
        <header className="h-24 border-b border-choco-200 flex items-center justify-between px-8 bg-white/40 backdrop-blur-xl sticky top-0 z-10">
          <div className="relative w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-choco-300" />
            <input
              type="text"
              placeholder={activeTab === 'produkty' ? "Szukaj produktów (nazwa, EAN)..." : "Szukaj surowców (globalnie)..."}
              className="w-full bg-choco-100/30 border border-choco-100 rounded-full py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-choco-500/50 transition-all placeholder:text-choco-300"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-4">
            {activeTab === 'surowce' && !searchTerm && !selectedCategory && (
              <button
                onClick={handleAddCategory}
                className="bg-white border border-choco-200 text-choco-700 hover:bg-choco-50 px-6 py-2.5 rounded-full text-sm font-semibold flex items-center gap-2 transition-all"
              >
                <FolderPlus className="w-4 h-4" />
                Dodaj kategorię
              </button>
            )}
            {activeTab === 'produkty' && (
              <button
                onClick={() => openAddProductModal(searchTerm ? 'inne' : selectedProductType)}
                className="bg-choco-800 hover:bg-choco-700 text-white px-6 py-2.5 rounded-full text-sm font-semibold flex items-center gap-2 shadow-lg shadow-choco-900/30 transition-all transform hover:scale-105 active:scale-95"
              >
                <Plus className="w-4 h-4" />
                Dodaj Produkt
              </button>
            )}
            {activeTab === 'surowce' && (
              <button
                onClick={() => setShowAddSurowiecModal(true)}
                className="bg-choco-800 hover:bg-choco-700 text-white px-6 py-2.5 rounded-full text-sm font-semibold flex items-center gap-2 shadow-lg shadow-choco-900/30 transition-all transform hover:scale-105 active:scale-95"
              >
                <Plus className="w-4 h-4" />
                Dodaj Surowiec
              </button>
            )}
          </div>
        </header>

        <section className="flex-1 p-8 overflow-auto custom-scrollbar">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-end justify-between mb-8">
              <div>
                <p className="text-gold-600 font-black text-[10px] uppercase tracking-[0.3em] mb-1">System Zarządzania</p>
                <div className="flex items-center gap-4">
                  {activeTab === 'surowce' && (selectedCategory || searchTerm) && (
                    <button
                      onClick={() => {
                        setSelectedCategory(null)
                        setSearchTerm('')
                      }}
                      className="p-2 bg-white border border-choco-100 rounded-full text-choco-400 hover:text-choco-800 transition-all shadow-sm"
                    >
                      <ArrowLeft className="w-5 h-5" />
                    </button>
                  )}
                  <h2 className="text-4xl font-black text-choco-800 tracking-tighter">
                    {activeTab === 'produkty' ? 'Katalog Wyrobów' :
                      (searchTerm ? 'Wyniki wyszukiwania' :
                        (selectedCategory ? selectedCategory : 'Baza Surowców'))}
                  </h2>
                </div>
              </div>
              <div className="text-right text-choco-600 text-sm font-black">
                {activeTab === 'produkty'
                  ? (searchTerm
                    ? `${filteredProdukty.length} POZYCJI`
                    : `${filteredTabItems.length} POZYCJI`)
                  : (searchTerm || selectedCategory
                    ? `${filteredSurowce.length} POZYCJI`
                    : `${categories.length} KATEGORII`)}
              </div>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
                {[1, 2, 3, 4, 5, 6].map(n => (
                  <div key={n} className="h-48 bg-white rounded-2xl border border-choco-100"></div>
                ))}
              </div>
            ) : activeTab === 'surowce' ? (
              <>
                {/* Cases: Global Search, Category Items, or Categories List */}
                {searchTerm ? (
                  // Global Search Results
                  <div className="flex flex-col gap-2">
                    {filteredSurowce.map(item => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setEditingSurowiec(item)
                          setShowAddSurowiecModal(true)
                        }}
                        className="bg-white border border-choco-100 rounded-xl px-6 py-4 hover:border-choco-400 hover:shadow-xl hover:shadow-choco-900/5 transition-all group cursor-pointer flex items-center justify-between"
                      >
                        <div className="flex items-center gap-4">
                          <div className="bg-choco-50 p-2 rounded-lg text-choco-600 group-hover:bg-choco-700 group-hover:text-white transition-colors">
                            <Database className="w-4 h-4" />
                          </div>
                          <div className="flex flex-col">
                            <span className="font-bold text-choco-800 group-hover:text-choco-900 transition-colors uppercase tracking-tight">
                              {item.nazwa} ({item.kategoria || 'Inne'})
                            </span>
                          </div>
                        </div>
                        <ChevronRight className="w-5 h-5 text-choco-200 group-hover:text-gold-600 transition-all transform group-hover:translate-x-1" />
                      </div>
                    ))}
                    {filteredSurowce.length === 0 && (
                      <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-choco-200">
                        <p className="text-choco-400 font-bold uppercase tracking-widest">Nie znaleziono surowców spełniających kryteria.</p>
                      </div>
                    )}
                  </div>
                ) : selectedCategory ? (
                  // Items in specific category
                  <div className="flex flex-col gap-2">
                    {filteredSurowce.map(item => (
                      <div
                        key={item.id}
                        onClick={() => {
                          setEditingSurowiec(item)
                          setShowAddSurowiecModal(true)
                        }}
                        className="bg-white border border-choco-100 rounded-xl px-6 py-4 hover:border-choco-400 hover:shadow-xl hover:shadow-choco-900/5 transition-all group cursor-pointer flex items-center justify-between"
                      >
                        <div className="flex items-center gap-4">
                          <div className="bg-choco-50 p-2 rounded-lg text-choco-600 group-hover:bg-choco-700 group-hover:text-white transition-colors">
                            <Database className="w-4 h-4" />
                          </div>
                          <span className="font-bold text-choco-800 group-hover:text-choco-900 transition-colors uppercase tracking-tight">
                            {item.nazwa}
                          </span>
                        </div>
                        <ChevronRight className="w-5 h-5 text-choco-200 group-hover:text-gold-600 transition-all transform group-hover:translate-x-1" />
                      </div>
                    ))}
                    {filteredSurowce.length === 0 && (
                      <div className="text-center py-20 bg-white rounded-3xl border border-dashed border-choco-200">
                        <p className="text-choco-400 font-bold uppercase tracking-widest">Brak surowców w tej kategorii.</p>
                      </div>
                    )}
                  </div>
                ) : (
                  // Categories List
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {categories.map(cat => (
                      <div
                        key={cat.name}
                        onClick={() => setSelectedCategory(cat.name)}
                        className="bg-white border border-choco-100 rounded-3xl p-8 hover:border-gold-500/50 hover:shadow-2xl hover:shadow-choco-900/10 transition-all group cursor-pointer flex flex-col items-center text-center relative overflow-hidden"
                      >
                        <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
                          <Database className="w-24 h-24" />
                        </div>
                        <div className="w-16 h-16 bg-choco-50 rounded-2xl flex items-center justify-center text-choco-600 mb-6 group-hover:bg-choco-800 group-hover:text-white transition-all shadow-inner">
                          <Database className="w-8 h-8" />
                        </div>
                        <h3 className="text-xl font-black text-choco-800 mb-2 uppercase tracking-tight group-hover:text-choco-950 transition-colors">
                          {cat.name} ({cat.count})
                        </h3>
                      </div>
                    ))}
                    {categories.length === 0 && (
                      <div className="col-span-full text-center py-20 bg-white rounded-3xl border border-dashed border-choco-200">
                        <p className="text-choco-400 font-bold uppercase tracking-widest">Baza surowców jest pusta.</p>
                      </div>
                    )}
                  </div>
                )}
              </>
            ) : searchTerm ? (
              // ---- SEARCH RESULTS (flat grid) ----
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                {filteredProdukty.map(item => (
                  <ProductCard key={item.ean || '~'} item={item} onClick={setSelectedProductEan} />
                ))}
                {filteredProdukty.length === 0 && (
                  <div className="col-span-full text-center py-20 bg-white rounded-3xl border border-dashed border-choco-200">
                    <p className="text-choco-400 font-bold uppercase tracking-widest">Nie znaleziono produktów.</p>
                  </div>
                )}
              </div>
            ) : (
              // ---- TABS CATALOG ----
              <>
                {/* Tab bar + kategoria filter */}
                <div className="flex flex-wrap items-center gap-3 mb-8">
                  {/* Type tabs */}
                  <div className="flex items-center gap-1 bg-white border border-choco-100 rounded-2xl p-1.5 shadow-sm">
                    {PRODUCT_TYPE_ORDER.map(typeKey => {
                      const count = (produktyByType[typeKey] || []).length
                      const isActive = selectedProductType === typeKey
                      return (
                        <button
                          key={typeKey}
                          onClick={() => {
                            setSelectedProductType(typeKey)
                            setSelectedKategoria('')
                          }}
                          className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-black uppercase tracking-wider transition-all ${isActive
                              ? 'bg-choco-800 text-white shadow-lg shadow-choco-900/20'
                              : 'text-choco-400 hover:text-choco-700 hover:bg-choco-50'
                            }`}
                        >
                          {PRODUCT_TYPE_LABELS[typeKey]}
                          <span className={`text-[10px] font-black px-1.5 py-0.5 rounded-full ${isActive ? 'bg-white/20 text-white' : 'bg-choco-100 text-choco-400'
                            }`}>
                            {count}
                          </span>
                        </button>
                      )
                    })}
                  </div>

                  {/* Kategoria filter — styled to match the type tabs pill */}
                  <div className={`flex items-center gap-1 bg-white border rounded-2xl p-1.5 shadow-sm transition-all ${selectedKategoria ? 'border-gold-400' : 'border-choco-100'
                    }`}>
                    <select
                      value={selectedKategoria}
                      onChange={(e) => setSelectedKategoria(e.target.value)}
                      className={`px-5 py-2.5 rounded-xl text-sm font-black uppercase tracking-wider focus:outline-none cursor-pointer transition-all appearance-none ${selectedKategoria
                          ? 'bg-choco-800 text-white shadow-lg shadow-choco-900/20'
                          : 'bg-transparent text-choco-400 hover:text-choco-700'
                        }`}
                    >
                      <option value="">Wszystkie kategorie</option>
                      <option value="Wielkanoc">Wielkanoc</option>
                      <option value="Boże Narodzenie">Boże Narodzenie</option>
                      <option value="Dzień Dziecka">Dzień Dziecka</option>
                      <option value="Walentynki">Walentynki</option>
                      <option value="Halloween">Halloween</option>
                      <option value="Całoroczne">Całoroczne</option>
                    </select>
                    {selectedKategoria && (
                      <button
                        onClick={() => setSelectedKategoria('')}
                        className="p-2 rounded-xl text-white/70 hover:text-white hover:bg-white/10 transition-all"
                        title="Wyczyść filtr"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Products grid for active tab */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                  {filteredTabItems.map(item => (
                    <ProductCard key={item.ean || '~'} item={item} onClick={setSelectedProductEan} />
                  ))}
                  {filteredTabItems.length === 0 && (
                    <div className="col-span-full text-center py-20 bg-white rounded-3xl border border-dashed border-choco-200">
                      <p className="text-choco-400 font-bold uppercase tracking-widest mb-4">
                        {selectedKategoria
                          ? `Brak produktów „${PRODUCT_TYPE_LABELS[selectedProductType]}" w kategorii „${selectedKategoria}".`
                          : `Brak produktów w kategorii „${PRODUCT_TYPE_LABELS[selectedProductType]}".`}
                      </p>
                      {!selectedKategoria && (
                        <button
                          onClick={() => openAddProductModal(selectedProductType)}
                          className="inline-flex items-center gap-2 text-sm font-semibold text-choco-500 hover:text-choco-800 border border-choco-200 hover:border-choco-400 bg-white hover:bg-choco-50 px-5 py-2.5 rounded-full transition-all"
                        >
                          <Plus className="w-4 h-4" />
                          Dodaj pierwszy produkt
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </section>

        {selectedProductEan && (
          <ProductDetails
            ean={selectedProductEan}
            onClose={() => setSelectedProductEan(null)}
            onRefresh={fetchData}
            notify={(msg, type) => setNotification({ message: msg, type })}
          />
        )}

        {showAddModal && (
          <AddProductModal
            initialProductType={addModalProductType}
            onClose={() => setShowAddModal(false)}
            onRefresh={fetchData}
            notify={(msg, type) => setNotification({ message: msg, type })}
          />
        )}

        {(showAddSurowiecModal || editingSurowiec) && (
          <AddSurowiecModal
            surowiec={editingSurowiec}
            onClose={() => {
              setShowAddSurowiecModal(false)
              setEditingSurowiec(null)
            }}
            onRefresh={fetchData}
            notify={(msg, type) => setNotification({ message: msg, type })}
          />
        )}

        {notification && (
          <Notification
            message={notification.message}
            type={notification.type}
            onClose={() => setNotification(null)}
          />
        )}
      </main>
    </div>
  )
}

export default App
