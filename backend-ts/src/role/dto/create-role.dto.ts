import { IsString, IsOptional, IsBoolean, IsArray, MaxLength } from 'class-validator';

export class CreateRoleDto {
  @IsString()
  @MaxLength(128)
  name!: string;

  @IsString()
  @MaxLength(64)
  code!: string;

  @IsOptional()
  @IsString()
  description?: string;

  @IsOptional()
  @IsArray()
  menu_ids?: number[];

  @IsOptional()
  @IsBoolean()
  is_system?: boolean = false;
}
