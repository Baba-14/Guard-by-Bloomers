import { Checker } from '@/components/Checker';
import { notFound } from 'next/navigation';
const valid=['message','screenshot','link','number','whatsapp','payment','call'] as const;
export default function Page({params,searchParams}:{params:{kind:string};searchParams:{input?:string;auto?:string}}){if(!valid.includes(params.kind as any))notFound(); return <Checker kind={params.kind as typeof valid[number]} initialInput={searchParams.input || ''} autoStart={searchParams.auto === '1'}/>}
