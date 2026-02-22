import React, { useEffect } from 'react'
import { X, CheckCircle, AlertTriangle, AlertCircle, Info } from 'lucide-react'

export default function Notification({ message, type = 'info', onClose }) {
    useEffect(() => {
        const timer = setTimeout(() => {
            onClose()
        }, 5000)
        return () => clearTimeout(timer)
    }, [onClose])

    const styles = {
        success: 'bg-green-50 border-green-200 text-green-700',
        error: 'bg-red-50 border-red-200 text-red-700',
        warning: 'bg-gold-50 border-gold-200 text-gold-700',
        info: 'bg-choco-50 border-choco-100 text-choco-700'
    }

    const Icons = {
        success: CheckCircle,
        error: AlertCircle,
        warning: AlertTriangle,
        info: Info
    }

    const Icon = Icons[type] || Info

    return (
        <div className={`fixed bottom-8 right-8 z-[100] flex items-center gap-4 px-6 py-4 rounded-2xl border backdrop-blur-xl shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-300 ${styles[type]}`}>
            <Icon className="w-6 h-6 shrink-0" />
            <div className="flex-1">
                <p className="font-bold text-sm">{type.toUpperCase()}</p>
                <p className="text-sm opacity-90">{message}</p>
            </div>
            <button onClick={onClose} className="p-1 hover:bg-black/10 rounded-full transition-colors">
                <X className="w-4 h-4" />
            </button>
        </div>
    )
}
