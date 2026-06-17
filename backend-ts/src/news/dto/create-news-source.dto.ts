import { IsString, IsOptional, IsInt, IsBoolean, IsEnum, MaxLength } from 'class-validator';
import { Type } from 'class-transformer';
import { NewsSourceType } from '../../common/constants/enums';

export class CreateNewsSourceDto {
  @IsString()
  @MaxLength(128)
  source_key!: string;

  @IsString()
  @MaxLength(128)
  name!: string;

  @IsEnum(NewsSourceType)
  source_type!: NewsSourceType;

  @IsString()
  @MaxLength(500)
  url!: string;

  @IsOptional()
  @IsString()
  category?: string;

  @IsOptional()
  @IsString()
  language?: string = 'en';

  @IsOptional()
  @Type(() => Number)
  @IsInt()
  fetch_interval_minutes?: number = 360;

  @IsOptional()
  @IsBoolean()
  is_enabled?: boolean = true;

  @IsOptional()
  extra?: Record<string, unknown>;
}
