/**
 * SE Primer tutor: deterministic Socratic question generator.
 * Not an LLM. Pure and testable; never sends student input to a server.
 */
export const stagePrompts = [
  'Bir geri dönüş planını güvenli kılmak için hangi değişiklikleri doğrulaman gerekir?',
  'Yeni sürümün en kritik kullanıcı akışını nasıl doğruladığını hangi kanıt gösterir?',
  'Bir hata ayıklama kaydında gerçekten gerekli olan kişisel bilgiler hangileridir?'
];

const patterns = [
  { id: 'answer_request', re: /(?:doğru|cevap|cevab[ıi]|şık|seçenek|buton|hangi\s+harf|hangisini\s+seç|a\s*m[ıi]|b\s*m[ıi])/i,
    questions: [
      'Bir mimari kararını savunmak için önce hangi teknik kanıtı ararsın?',
      'Bir değişikliği yayına almak için hangi ölçülebilir kanıt sana güven verir?',
      'Bir kaydı paylaşmadan önce gerçekten ihtiyaç duyulan alanları nasıl belirlersin?'
    ] },
  { id: 'confusion', re: /(?:anlamadım|bilmiyorum|hiçbir şey|kafam karıştı|zor geliyor)/i,
    questions: [
      'Önce şunu düşün: Eski ve yeni sürümün ortak kullandığı veride ne değişmiş olabilir?',
      'Önce şunu düşün: Hasta randevusunu almak için hangi tek işlem mutlaka çalışmalı?',
      'Önce şunu düşün: Bir hasta adını görmeden hatanın türünü anlayabilir misin?'
    ] },
  { id: 'authority', re: /(?:yönetici|patron|amir|herkes|ekip\s+diyor)/i,
    questions: [
      'Fikir birliğinden bağımsız olarak hangi teknik kanıt kararını değiştirirdi?',
      'Bir üstüne hangi test sonucunu göstererek riski somutlaştırabilirsin?',
      'Yetki ve erişim sınırlarını hangi ilkeye göre değerlendirirsin?'
    ] },
  { id: 'time_pressure', re: /(?:zamanımız|zaman\s+(?:yok|dar)|süre|acele|hemen|hızl[ıa])/i,
    questions: [
      'Az zamanın varken geri alınması zor olan değişikliği nasıl tespit edersin?',
      'Süren kısıtlıysa en yüksek riski gösteren kısa kontrol hangisi olurdu?',
      'Acil durumlarda bile paylaşılan veri miktarını nasıl sınırlarsın?'
    ] },
  { id: 'schema', re: /(?:şema|schema|veritabanı|database|rollback|geri\s+dön|sürüm|yama)/i,
    questions: [
      'Yeni veritabanı şeması eski uygulamanın beklentileriyle uyumlu mu; bunu nasıl ölçersin?',
      'Sürüm değişikliğinin hangi kritik akışları etkilediğini nasıl seçersin?',
      'Uygulama sürümleri arasında log alanlarının hassasiyeti değişmiş olabilir mi?'
    ] },
  { id: 'testing', re: /(?:smoke|test|regresyon|giriş\s+ekranı|açıl|üretim)/i,
    questions: [
      'Uyguladığın düzeltmenin mevcut işlevleri bozmadığını hangi test gösterir?',
      'Smoke testte yalnızca açılışı mı yoksa kritik randevu akışını mı gözlemlemelisin; hangi kanıtın var?',
      'Hata kayıtlarında kişisel veri görünmediğini nasıl doğrularsın?'
    ] },
  { id: 'privacy', re: /(?:hasta|isim|adını|log|kvkk|slack|paylaş|kişisel|veri|sakla)/i,
    questions: [
      'Hata incelemesine ait kayıtlarda hangi bilgiler gerçekten gereklidir?',
      'Test verisiyle gerçek kullanıcı verisini ayırmak için ne yapabilirsin?',
      'Bir log satırında kimliği belirleyen alanları nasıl fark edersin?'
    ] },
];

export function tutorRespond(message, stage = 0, profile = {}) {
  const index = Math.min(2, Math.max(0, Number(stage) || 0));
  const text = String(message || '').trim().slice(0, 500);
  const matched = patterns.find(p => p.re.test(text));
  const category = matched?.id || 'general';
  const question = matched ? matched.questions[index] : stagePrompts[index];
  const prefix = profile.level === 'beginner' ? 'Küçük bir adımla ilerleyelim. ' : '';
  const role = profile.role === 'tester' ? 'Test mühendisi bakış açısıyla: ' : profile.role === 'lead' ? 'Teknik lider bakış açısıyla: ' : '';
  return { category, text: `${prefix}${role}${question}` };
}
