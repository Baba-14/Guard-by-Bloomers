import { Checker } from '@/components/Checker';
import { notFound } from 'next/navigation';
const valid=['message','screenshot','link','number','whatsapp','payment','call'] as const;
export default async function Page({params,searchParams}:{params:Promise<{kind:string}>;searchParams:Promise<{input?:string;auto?:string}>}){const route=await params;const query=await searchParams;if(!valid.includes(route.kind as any))notFound(); return <Checker kind={route.kind as typeof valid[number]} initialInput={query.input || ''} autoStart={query.auto === '1'}/>}
