import { redirect } from 'next/navigation';

export default function Home() {
  // ダッシュボードページにリダイレクト
  redirect('/home');
}