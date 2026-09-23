import { Checker } from '@/components/Checker';
import { notFound } from 'next/navigation';
const valid=['message','screenshot','link','number','payment','call'] as const;
export default function Page({params}:{params:{kind:string}}){if(!valid.includes(params.kind as any))notFound(); return <Checker kind={params.kind as typeof valid[number]}/>}
