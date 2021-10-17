-- phpMyAdmin SQL Dump
-- version 4.5.1
-- http://www.phpmyadmin.net
--
-- Host: 127.0.0.1
-- Generation Time: 12-Set-2021 às 20:16
-- Versão do servidor: 10.1.9-MariaDB
-- PHP Version: 5.6.15

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `cadastro_ong`
--

-- --------------------------------------------------------

--
-- Estrutura da tabela `conjugue`
--

CREATE TABLE `conjugue` (
  `id_conjugue` int(11) NOT NULL,
  `nome` varchar(60) CHARACTER SET latin1 NOT NULL,
  `data_nasc` date NOT NULL,
  `sexo` enum('M','F') CHARACTER SET latin1 NOT NULL,
  `escolaridade` varchar(25) CHARACTER SET latin1 NOT NULL,
  `nis` char(13) NOT NULL,
  `rg` int(9) NOT NULL,
  `cpf` char(11) NOT NULL,
  `titulo` char(12) NOT NULL,
  `zona` int(3) NOT NULL,
  `secao` int(4) NOT NULL,
  `celular` char(11) CHARACTER SET latin1 NOT NULL,
  `e-mail` varchar(30) CHARACTER SET latin1 NOT NULL,
  `facebook` varchar(20) CHARACTER SET latin1 NOT NULL,
  `profissao` varchar(30) CHARACTER SET latin1 NOT NULL,
  `renda` char(10) CHARACTER SET latin1 NOT NULL,
  `fk_titularconj` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estrutura da tabela `dependente`
--

CREATE TABLE `dependente` (
  `id_dep` int(6) NOT NULL,
  `Nome` varchar(60) CHARACTER SET latin1 NOT NULL,
  `data_nasc` date NOT NULL,
  `NIS` char(13) NOT NULL,
  `Renda` varchar(10) CHARACTER SET latin1 NOT NULL,
  `fk_titulardep` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estrutura da tabela `programas_habitacionais`
--

CREATE TABLE `programas_habitacionais` (
  `id_prog` int(11) NOT NULL,
  `Incrição` enum('Sim','Não') CHARACTER SET latin1 NOT NULL,
  `Qual_in` varchar(20) CHARACTER SET latin1 NOT NULL,
  `N_inscrição` char(15) CHARACTER SET latin1 NOT NULL,
  `Outra_associação` enum('Sim','Não') CHARACTER SET latin1 NOT NULL,
  `Qual_associação` varchar(20) CHARACTER SET latin1 NOT NULL,
  `Total_renda` varchar(20) CHARACTER SET latin1 NOT NULL,
  `fk_titularprog` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- Estrutura da tabela `titular`
--

CREATE TABLE `titular` (
  `matricula` int(11) NOT NULL,
  `nome` varchar(60) CHARACTER SET latin1 NOT NULL,
  `endereco` varchar(50) CHARACTER SET latin1 NOT NULL,
  `complemeto` varchar(20) CHARACTER SET latin1 NOT NULL,
  `bairro` varchar(15) CHARACTER SET latin1 NOT NULL,
  `cep` char(8) CHARACTER SET latin1 NOT NULL,
  `cidade` varchar(20) CHARACTER SET latin1 NOT NULL,
  `estado` char(2) CHARACTER SET latin1 NOT NULL,
  `naturalidade` varchar(20) CHARACTER SET latin1 NOT NULL,
  `data_nasc` date NOT NULL,
  `estado_civil` varchar(10) CHARACTER SET latin1 NOT NULL,
  `sexo` enum('M','F') CHARACTER SET latin1 NOT NULL,
  `escolaridade` varchar(25) CHARACTER SET latin1 NOT NULL,
  `profissao` varchar(30) CHARACTER SET latin1 NOT NULL,
  `renda` varchar(10) CHARACTER SET latin1 NOT NULL,
  `telefone` char(10) CHARACTER SET latin1 NOT NULL,
  `celular` char(11) CHARACTER SET latin1 NOT NULL,
  `telefone_rec` char(11) CHARACTER SET latin1 NOT NULL,
  `e-mail` varchar(30) CHARACTER SET latin1 NOT NULL,
  `facebook` varchar(25) CHARACTER SET latin1 NOT NULL,
  `nis` char(13) NOT NULL,
  `rg` int(9) NOT NULL,
  `cpf` char(11) NOT NULL,
  `titulo` char(12) NOT NULL,
  `zona` int(3) NOT NULL,
  `secao` int(4) NOT NULL,
  `moradia` enum('Aluguel','Cedida','Favela','Ocupação','Área livre','Área de risco') CHARACTER SET latin1 NOT NULL,
  `ativo` enum('Sim','Não') CHARACTER SET latin1 NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `conjugue`
--
ALTER TABLE `conjugue`
  ADD PRIMARY KEY (`id_conjugue`),
  ADD KEY `fk_titularconj` (`fk_titularconj`);

--
-- Indexes for table `dependente`
--
ALTER TABLE `dependente`
  ADD PRIMARY KEY (`id_dep`),
  ADD KEY `fk_titulardep` (`fk_titulardep`);

--
-- Indexes for table `programas_habitacionais`
--
ALTER TABLE `programas_habitacionais`
  ADD PRIMARY KEY (`id_prog`),
  ADD KEY `fk_titularprog` (`fk_titularprog`);

--
-- Indexes for table `titular`
--
ALTER TABLE `titular`
  ADD PRIMARY KEY (`matricula`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `conjugue`
--
ALTER TABLE `conjugue`
  MODIFY `id_conjugue` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
--
-- AUTO_INCREMENT for table `dependente`
--
ALTER TABLE `dependente`
  MODIFY `id_dep` int(6) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
--
-- AUTO_INCREMENT for table `programas_habitacionais`
--
ALTER TABLE `programas_habitacionais`
  MODIFY `id_prog` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
--
-- AUTO_INCREMENT for table `titular`
--
ALTER TABLE `titular`
  MODIFY `matricula` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;
--
-- Constraints for dumped tables
--

--
-- Limitadores para a tabela `conjugue`
--
ALTER TABLE `conjugue`
  ADD CONSTRAINT `fk_titularconj` FOREIGN KEY (`fk_titularconj`) REFERENCES `titular` (`matricula`) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Limitadores para a tabela `dependente`
--
ALTER TABLE `dependente`
  ADD CONSTRAINT `titulardep` FOREIGN KEY (`fk_titulardep`) REFERENCES `titular` (`matricula`) ON DELETE NO ACTION ON UPDATE NO ACTION;

--
-- Limitadores para a tabela `programas_habitacionais`
--
ALTER TABLE `programas_habitacionais`
  ADD CONSTRAINT `fk_titularprog` FOREIGN KEY (`fk_titularprog`) REFERENCES `titular` (`matricula`) ON DELETE NO ACTION ON UPDATE NO ACTION;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
