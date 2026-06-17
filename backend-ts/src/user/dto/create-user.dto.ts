import { IsString, IsOptional, IsBoolean, IsEmail, IsArray, MaxLength } from 'class-validator';

export class CreateUserDto {
  @IsString()
  @MaxLength(64)
  username!: string;

  @IsString()
  @MaxLength(128)
  password!: string;

  @IsOptional()
  @IsEmail()
  @MaxLength(255)
  email?: string;

  @IsOptional()
  @IsString()
  @MaxLength(32)
  phone?: string;

  @IsOptional()
  @IsString()
  @MaxLength(128)
  nickname?: string;

  @IsOptional()
  @IsArray()
  role_ids?: number[];

  @IsOptional()
  @IsBoolean()
  is_superuser?: boolean = false;
}
