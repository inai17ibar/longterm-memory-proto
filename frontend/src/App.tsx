import { useState, useEffect, useRef } from 'react'
import { Send, User, Brain, Trash2, Info, Download } from 'lucide-react'
import { Button } from './components/ui/button'
import { Input } from './components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card'
import { ScrollArea } from './components/ui/scroll-area'
import { Alert, AlertDescription } from './components/ui/alert'
import { Badge } from './components/ui/badge'

interface Message {
  user_message: string
  ai_response: string
  timestamp: string
}

interface UserInfo {
  user_id: string
  name?: string
  hobbies?: string[]
  job?: string
  other_info?: Record<string, any>
  memory_items?: Array<{
    type: string
    content: string
    timestamp: string
    source: string
  }>
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentMessage, setCurrentMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [userId, setUserId] = useState<string>('')
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
  const [error, setError] = useState<string>('')
  const [isExporting, setIsExporting] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000'

  useEffect(() => {
    let storedUserId = localStorage.getItem('counseling_user_id')
    if (!storedUserId) {
      storedUserId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
      localStorage.setItem('counseling_user_id', storedUserId)
    }
    setUserId(storedUserId)
    loadUserData(storedUserId)
    loadConversationHistory(storedUserId)
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const loadUserData = async (uid: string) => {
    try {
      const response = await fetch(`${API_URL}/api/users/${uid}`)
      if (response.ok) {
        const userData = await response.json()
        setUserInfo(userData)
      }
    } catch (error) {
      console.log('No existing user data found')
    }
  }

  const loadConversationHistory = async (uid: string) => {
    try {
      const response = await fetch(`${API_URL}/api/conversations/${uid}`)
      if (response.ok) {
        const data = await response.json()
        setMessages(data.conversations || [])
      }
    } catch (error) {
      console.error('Failed to load conversation history:', error)
    }
  }

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return

    setIsLoading(true)
    setError('')

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          message: currentMessage
        })
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data = await response.json()
      
      const newMessage: Message = {
        user_message: currentMessage,
        ai_response: data.response,
        timestamp: new Date().toISOString()
      }

      setMessages(prev => [...prev, newMessage])
      setCurrentMessage('')

      if (data.user_info_updated) {
        loadUserData(userId)
      }

    } catch (error) {
      setError('メッセージの送信に失敗しました。もう一度お試しください。')
      console.error('Error sending message:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const clearConversation = async () => {
    if (!window.confirm('会話履歴を削除しますか？この操作は取り消せません。')) return

    try {
      await fetch(`${API_URL}/api/users/${userId}`, {
        method: 'DELETE'
      })
      setMessages([])
      setUserInfo(null)
      localStorage.removeItem('counseling_user_id')
      const newUserId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
      localStorage.setItem('counseling_user_id', newUserId)
      setUserId(newUserId)
    } catch (error) {
      setError('データの削除に失敗しました。')
    }
  }

  const exportConversations = async () => {
    setIsExporting(true)
    try {
      const response = await fetch(`${API_URL}/api/export-conversations/${userId}`)
      if (response.ok) {
        const data = await response.json()
        
        const blob = new Blob([data.csv_data], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = data.filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        setError('会話履歴のエクスポートに失敗しました')
      }
    } catch (error) {
      setError('エクスポート中にエラーが発生しました')
    } finally {
      setIsExporting(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2 flex items-center justify-center gap-2">
            <Brain className="text-blue-600" />
            メンタルヘルス カウンセリング
          </h1>
          <p className="text-gray-600">あなたの心の健康をサポートします</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <Card className="h-[600px] flex flex-col">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="w-5 h-5" />
                  カウンセリング チャット
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <ScrollArea className="flex-1 pr-4">
                  <div className="space-y-4">
                    {messages.length === 0 && (
                      <div className="text-center text-gray-500 py-8">
                        <Brain className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                        <p>こんにちは。お話をお聞かせください。</p>
                        <p className="text-sm mt-2">あなたの名前、趣味、お仕事などについて教えていただければ、より良いサポートができます。</p>
                      </div>
                    )}
                    {messages.map((message, index) => (
                      <div key={index} className="space-y-4 mb-6">
                        <div className="flex justify-end">
                          <div className="bg-blue-500 text-white p-3 rounded-lg max-w-sm md:max-w-md lg:max-w-lg xl:max-w-xl">
                            <p className="whitespace-pre-wrap">{message.user_message}</p>
                          </div>
                        </div>
                        <div className="flex justify-start">
                          <div className="bg-gray-100 p-3 rounded-lg max-w-sm md:max-w-md lg:max-w-lg xl:max-w-xl">
                            <div className="flex items-center gap-2 mb-2">
                              <Brain className="w-4 h-4 text-blue-600" />
                              <span className="text-sm font-medium text-blue-600">カウンセラー</span>
                            </div>
                            <p className="whitespace-pre-wrap">{message.ai_response}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div ref={messagesEndRef} />
                </ScrollArea>

                {error && (
                  <Alert className="mb-4 border-red-200 bg-red-50">
                    <AlertDescription className="text-red-700">
                      {error}
                    </AlertDescription>
                  </Alert>
                )}

                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-2">よくある相談:</p>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      onClick={() => setCurrentMessage("どうやって気分転換をすればいいですか？")}
                      disabled={isLoading}
                      className="text-xs"
                    >
                      気分転換の方法
                    </Button>
                    <Button
                      onClick={() => setCurrentMessage("とても不安です")}
                      disabled={isLoading}
                      className="text-xs"
                    >
                      不安な気持ち
                    </Button>
                    <Button
                      onClick={() => setCurrentMessage("うつのせいか体を動かすこともつらいです")}
                      disabled={isLoading}
                      className="text-xs"
                    >
                      体調の不調
                    </Button>
                    <Button
                      onClick={() => setCurrentMessage("仕事に復帰するのが怖いです")}
                      disabled={isLoading}
                      className="text-xs"
                    >
                      復職への不安
                    </Button>
                    <Button
                      onClick={() => setCurrentMessage("眠れない日が続いています")}
                      disabled={isLoading}
                      className="text-xs"
                    >
                      睡眠の問題
                    </Button>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Input
                    value={currentMessage}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCurrentMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="メッセージを入力してください..."
                    disabled={isLoading}
                    className="flex-1"
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={isLoading || !currentMessage.trim()}
                    className="px-4"
                  >
                    {isLoading ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Info className="w-5 h-5" />
                  記憶された情報
                </CardTitle>
              </CardHeader>
              <CardContent>
                {userInfo ? (
                  <div className="space-y-3">
                    {userInfo.name && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">名前:</span>
                        <p className="text-sm">{userInfo.name}</p>
                      </div>
                    )}
                    {userInfo.job && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">職業:</span>
                        <p className="text-sm">{userInfo.job}</p>
                      </div>
                    )}
                    {userInfo.hobbies && userInfo.hobbies.length > 0 && (
                      <div>
                        <span className="text-sm font-medium text-gray-600">趣味:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {userInfo.hobbies.map((hobby, index) => (
                            <Badge key={index} className="text-xs">
                              {hobby}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    {userInfo.other_info && Object.keys(userInfo.other_info).length > 0 && (
                      <div className="space-y-2">
                        {userInfo.other_info.age && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">年齢:</span>
                            <p className="text-sm">{userInfo.other_info.age}歳</p>
                          </div>
                        )}
                        {userInfo.other_info.location && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">居住地:</span>
                            <p className="text-sm">{userInfo.other_info.location}</p>
                          </div>
                        )}
                        {userInfo.other_info.family && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">家族:</span>
                            <p className="text-sm">{userInfo.other_info.family}</p>
                          </div>
                        )}
                        {userInfo.memory_items && userInfo.memory_items.filter(item => item.type === 'concerns').length > 0 && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">悩み・心配事:</span>
                            <div className="space-y-1 mt-1">
                              {userInfo.memory_items
                                .filter(item => item.type === 'concerns')
                                .map((item, index) => (
                                  <p key={index} className="text-sm text-orange-700">• {item.content}</p>
                                ))}
                            </div>
                          </div>
                        )}
                        {userInfo.other_info.goals && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">目標・願望:</span>
                            <p className="text-sm text-green-700">{userInfo.other_info.goals}</p>
                          </div>
                        )}
                        {userInfo.other_info.personality && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">性格:</span>
                            <p className="text-sm">{userInfo.other_info.personality}</p>
                          </div>
                        )}
                        {userInfo.other_info.experiences && (
                          <div>
                            <span className="text-sm font-medium text-gray-600">重要な体験:</span>
                            <p className="text-sm">{userInfo.other_info.experiences}</p>
                          </div>
                        )}
                        {Object.entries(userInfo.other_info || {}).filter(([key]) => 
                          !['age', 'location', 'family', 'concerns', 'goals', 'personality', 'experiences'].includes(key)
                        ).map(([key, value]) => (
                          <div key={key}>
                            <span className="text-sm font-medium text-gray-600">{key}:</span>
                            <p className="text-sm">{String(value)}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">
                    まだ情報が記録されていません。会話を通じて情報を教えてください。
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">設定</CardTitle>
              </CardHeader>
              <CardContent>
                <Button 
                  onClick={clearConversation}
                  className="w-full flex items-center gap-2 mb-2"
                >
                  <Trash2 className="w-4 h-4" />
                  会話履歴を削除
                </Button>
                <Button 
                  onClick={exportConversations}
                  disabled={isExporting}
                  className="w-full flex items-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  {isExporting ? 'エクスポート中...' : '会話履歴をCSVでダウンロード'}
                </Button>
                <p className="text-xs text-gray-500 mt-2">
                  ユーザーID: {userId.slice(-8)}...
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
